# -*- coding: utf-8 -*-
import logging
import os

import arabic_reshaper
from bidi.algorithm import get_display

from kivy.app import App
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.screenmanager import (
    FadeTransition,
    Screen,
    ScreenManager,
)
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

from calculations import (
    ISOTOPES,
    boundary_estimate,
    decay,
    exposure_seconds,
    number,
    xray_distance,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ORANGE = (1, .45, 0, 1)
INACTIVE = (.16, .18, .22, 1)


def get_asset(filename):
    for folder in (BASE_DIR, os.path.join(BASE_DIR, 'assets')):
        path = os.path.join(folder, filename)

        if os.path.isfile(path):
            return path

    return None


FONT_PATH = (
    get_asset('Vazirmatn-Regular.ttf')
    or get_asset('font.ttf')
)

FONT_KW = {'font_name': FONT_PATH} if FONT_PATH else {}


def fa(text):
    if not text:
        return ''

    return get_display(arabic_reshaper.reshape(str(text)))


class SafeCard(BoxLayout):
    def __init__(
        self,
        bg_color=(.10, .12, .15, 1),
        radius=10,
        **kwargs,
    ):
        super().__init__(**kwargs)

        with self.canvas.before:
            Color(*bg_color)
            self.rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(radius)],
            )

        self.bind(
            pos=self._update_rect,
            size=self._update_rect,
        )

    def _update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size


class WrappedLabel(Label):
    """Wrap long labels instead of clipping them."""

    def __init__(self, text='', **kwargs):
        kwargs.setdefault('font_size', sp(13))
        kwargs.setdefault('color', (.85, .88, .91, 1))
        kwargs.setdefault('halign', 'right')

        super().__init__(
            text=fa(text),
            size_hint_y=None,
            **FONT_KW,
            **kwargs,
        )

        self.bind(
            width=self._wrap,
            texture_size=self._fit,
        )

        self._wrap()
        self._fit()

    def _wrap(self, *args):
        self.text_size = (
            max(dp(1), self.width - dp(12)),
            None,
        )

    def _fit(self, *args):
        self.height = max(
            dp(26),
            self.texture_size[1] + dp(12),
        )


class SafeInput(TextInput):
    def __init__(self, **kwargs):
        super().__init__(
            multiline=False,
            size_hint_y=None,
            height=dp(48),
            background_normal='',
            background_active='',
            background_color=(.05, .06, .08, 1),
            foreground_color=(1, 1, 1, 1),
            cursor_color=ORANGE,
            font_size=sp(16),
            halign='center',
            padding=[dp(6), dp(10)],
            write_tab=False,
            **FONT_KW,
            **kwargs,
        )


class CalculationScreen(Screen):
    def __init__(self, app, title, **kwargs):
        super().__init__(**kwargs)

        self.app = app
        self.inputs = {}
        self.titles = {}
        self._ready = False

        scroll = ScrollView(do_scroll_x=False)

        self.content = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            padding=dp(12),
            spacing=dp(10),
        )

        self.content.bind(
            minimum_height=self.content.setter('height')
        )

        self.content.add_widget(
            WrappedLabel(
                title,
                color=ORANGE,
                bold=True,
            )
        )

        self.source_label = WrappedLabel('')
        self.content.add_widget(self.source_label)

        scroll.add_widget(self.content)
        self.add_widget(scroll)

        app.bind(current_source=self._source_changed)

    def field(self, key, title, default=''):
        card = SafeCard(
            orientation='vertical',
            padding=dp(8),
            size_hint_y=None,
            spacing=dp(4),
        )

        card.bind(minimum_height=card.setter('height'))
        card.add_widget(WrappedLabel(title))

        widget = SafeInput(text=default)

        self.inputs[key] = widget
        self.titles[key] = title

        card.add_widget(widget)
        self.content.add_widget(card)

        widget.bind(text=self.calc)

    def note(self, text):
        self.content.add_widget(
            WrappedLabel(
                text,
                font_size=sp(12),
                color=(1, .78, .35, 1),
            )
        )

    def finish(self):
        card = SafeCard(
            orientation='vertical',
            size_hint_y=None,
            padding=dp(10),
            bg_color=(.06, .12, .10, 1),
        )

        card.bind(minimum_height=card.setter('height'))

        self.result = WrappedLabel(
            '—',
            font_size=sp(20),
        )
        self.details = WrappedLabel(
            '',
            font_size=sp(12),
        )

        card.add_widget(self.result)
        card.add_widget(self.details)
        self.content.add_widget(card)

        self._ready = True
        self.calc()

    def value(self, key, positive=False):
        return number(
            self.inputs[key].text,
            self.titles[key],
            positive,
        )

    def _source_changed(self, *args):
        self.calc()

    def on_pre_enter(self, *args):
        self.calc()

    def calc(self, *args):
        if not self._ready:
            return

        self.source_label.text = fa(
            f'ایزوتوپ انتخاب‌شده: {self.app.current_source}'
        )

        # Clear stale results before evaluating the new input.
        self.result.text = fa('—')
        self.details.text = ''

        try:
            result, details = self.compute()

            self.result.color = (.65, .95, .80, 1)
            self.result.text = fa(result)
            self.details.text = fa(details)

        except ValueError as exc:
            self.result.color = (1, .65, .4, 1)
            self.result.text = fa('ورودی یا نتیجه نامعتبر')
            self.details.text = fa(str(exc))

        except OverflowError:
            self.result.text = fa(
                'عدد خارج از محدوده محاسبه است'
            )

        except Exception:
            logging.exception(
                'Calculation failed on %s',
                self.name,
            )
            self.result.text = fa(
                'خطای داخلی؛ گزارش برنامه را بررسی کنید'
            )

    def compute(self):
        raise NotImplementedError


class SafetyScreen(CalculationScreen):
    def __init__(self, app, **kwargs):
        super().__init__(
            app,
            'برآورد فاصله با مدل ساده گاما',
            **kwargs,
        )

        self.field(
            'activity',
            'اکتیویته (Ci)',
            '40',
        )
        self.field(
            'dose',
            'نرخ دوز هدف (µSv/h) ـ مطابق طرح مصوب',
            '2.5',
        )
        self.field(
            'shield',
            'ضخامت سرب در مسیر پرتو (mm)',
            '0',
        )

        self.note(
            'صرفاً برآورد مدل نقطه‌ای؛ نه تعیین مرز ایمن. '
            'داده‌های ایزوتوپ از کد اولیه هستند و مستقلاً '
            'تأیید نشده‌اند. تبدیل واحد دوز تقریبی است. '
            'پراکندگی، buildup، نشتی و هندسه واقعی لحاظ نشده‌اند.'
        )

        self.note(
            'ضخامت کولیماتور برای دهانه خروجی پرتو قابل استفاده نیست. '
            'فاصله مجاز اپراتور از این مدل تعیین نمی‌شود. '
            'مرزبندی نیازمند طرح مصوب، مسئول حفاظت پرتویی '
            'و اندازه‌گیری با دستگاه مناسب و کالیبره است.'
        )

        self.finish()

    def compute(self):
        distance, transmission = boundary_estimate(
            self.app.current_source,
            self.value('activity'),
            self.value('dose', True),
            self.value('shield'),
        )

        return (
            f'فاصله مدل: {distance:.3g} متر',
            f'ضریب عبور مدل سرب: {transmission:.4g} | '
            'این نتیجه تأیید ایمنی نیست.',
        )


class XRayScreen(CalculationScreen):
    def __init__(self, app, **kwargs):
        super().__init__(
            app,
            'ایکس‌ری: برآورد از نرخ دوز اندازه‌گیری‌شده',
            **kwargs,
        )

        self.field(
            'rate',
            'نرخ دوز مرجع اندازه‌گیری‌شده (µSv/h)',
        )
        self.field(
            'distance',
            'فاصله اندازه‌گیری از کانون (m)',
        )
        self.field(
            'target',
            'نرخ دوز هدف (µSv/h) ـ مطابق طرح مصوب',
        )

        self.note(
            'فرمول تجربی بدون مرجعِ کد اولیه حذف شد. '
            'نرخ مرجع باید با ابزار مناسب و کالیبره، '
            'برای همان kV، جریان، فیلتراسیون، جهت و شرایط کار '
            'اندازه‌گیری شده باشد. '
            'برای پرتو پالسی از ابزار مناسب آن استفاده شود.'
        )

        self.note(
            'این صفحه به انتخاب ایزوتوپ وابسته نیست. '
            'مدل فقط قانون عکس مجذور فاصله در هندسه مناسب '
            'و بدون تغییر حفاظ است؛ پراکندگی و نشتی واقعی '
            'را تضمین نمی‌کند. '
            'مرز نهایی باید در محل اندازه‌گیری و تأیید شود.'
        )

        self.finish()

    def compute(self):
        distance = xray_distance(
            self.value('rate', True),
            self.value('distance', True),
            self.value('target', True),
        )

        return (
            f'فاصله برآوردی: {distance:.3g} متر',
            'صرفاً برون‌یابی نرخ دوز؛ نه تأیید ایمنی.',
        )


class DecayScreen(CalculationScreen):
    def __init__(self, app, **kwargs):
        super().__init__(
            app,
            'محاسبه واپاشی بر اساس روز',
            **kwargs,
        )

        self.field(
            'initial',
            'اکتیویته اولیه (Ci)',
            '80',
        )
        self.field(
            'days',
            'روزهای سپری‌شده',
            '30',
        )

        self.note(
            'نیمه‌عمرها از کد اولیه منتقل شده‌اند؛ '
            'برای کار عملی با گواهی چشمه و منابع معتبر تطبیق دهید. '
            'محاسبه خودکار تاریخ امروز انجام نمی‌شود؛ '
            'تعداد روز را وارد کنید.'
        )

        self.finish()

    def compute(self):
        initial = self.value('initial')

        activity, percent = decay(
            self.app.current_source,
            initial,
            self.value('days'),
        )

        if initial:
            info = f'افت نسبت به مقدار اولیه: {percent:.2f}٪'
        else:
            info = 'برای مقدار اولیه صفر، درصد افت تعریف نمی‌شود.'

        return f'{activity:.6g} Ci', info


class ExposureScreen(CalculationScreen):
    def __init__(self, app, **kwargs):
        super().__init__(
            app,
            'زمان پرتودهی از اکسپوژر مرجع تأییدشده',
            **kwargs,
        )

        self.reference_source = app.current_source

        self.field(
            'time',
            'زمان مرجع تأییدشده (ثانیه)',
        )
        self.field(
            'ref_activity',
            'اکتیویته در اکسپوژر مرجع (Ci)',
        )
        self.field(
            'ref_sfd',
            'فاصله SFD مرجع (cm)',
        )
        self.field(
            'activity',
            'اکتیویته فعلی (Ci)',
            '40',
        )
        self.field(
            'sfd',
            'فاصله SFD جدید (cm)',
            '50',
        )

        self.note(
            'مرجع باید برای همین ایزوتوپ، جنس و ضخامت عبوری، '
            'فیلم، دانسیته هدف، اسکرین، شرایط ظهور '
            'و آرایش پرتودهی باشد. '
            'فقط تغییر اکتیویته و SFD مقیاس می‌شود؛ '
            'تغییر هندسه ممکن است به تأیید مجدد روش نیاز داشته باشد.'
        )

        self.note(
            'ضریب تعریف‌نشده factor حذف شد؛ '
            'بدون مرجع معتبر، زمان قابل محاسبه نیست. '
            'با تغییر ایزوتوپ، ورودی‌های مرجع پاک می‌شوند '
            'تا مرجع قبلی اشتباه استفاده نشود.'
        )

        self.finish()

    def _source_changed(self, *args):
        source = self.app.current_source

        if source != self.reference_source:
            self.reference_source = source

            for key in ('time', 'ref_activity', 'ref_sfd'):
                self.inputs[key].text = ''

        super()._source_changed(*args)

    def compute(self):
        seconds = exposure_seconds(
            self.value('time', True),
            self.value('ref_activity', True),
            self.value('ref_sfd', True),
            self.value('activity', True),
            self.value('sfd', True),
        )

        return (
            f'زمان مقیاس‌شده: {seconds:.6g} ثانیه',
            'تخمین مبتنی بر مرجع؛ نه زمان دقیق یا تضمین کیفیت فیلم.',
        )


class IsotopeInfoScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        scroll = ScrollView(do_scroll_x=False)

        content = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            padding=dp(12),
            spacing=dp(10),
        )

        content.bind(
            minimum_height=content.setter('height')
        )

        content.add_widget(
            WrappedLabel(
                'داده‌های زیر از نسخه اولیه منتقل شده‌اند '
                'و مستقلاً اعتبارسنجی نشده‌اند. '
                'HVL ثابت، مدل ساده است و برای طراحی حفاظ کافی نیست.',
                color=(1, .78, .35, 1),
            )
        )

        for key, data in ISOTOPES.items():
            card = SafeCard(
                orientation='vertical',
                size_hint_y=None,
                padding=dp(8),
            )

            card.bind(
                minimum_height=card.setter('height')
            )

            lines = (
                f"{data['name']} ({key})",
                f"ثابت گامای ورودی: {data['gamma']} R·m²/(Ci·h)",
                f"انرژی درج‌شده: {data['energy']} | "
                f"نیمه‌عمر: {data['half_life']} روز",
                f"HVL سرب: {data['hvl_pb']} mm | "
                f"HVL فولاد: {data['hvl_fe']} mm",
            )

            for text in lines:
                card.add_widget(WrappedLabel(text))

            content.add_widget(card)

        scroll.add_widget(content)
        self.add_widget(scroll)


class NDTMainApp(App):
    current_source = StringProperty('Ir-192')

    def build(self):
        self.title = 'رادیوگرافی صنعتی ـ برآورد آموزشی'
        Window.clearcolor = (.05, .06, .08, 1)

        root = BoxLayout(orientation='vertical')

        header = SafeCard(
            size_hint_y=None,
            height=dp(84),
            padding=dp(8),
        )

        logo = get_asset('logo.png')

        if logo:
            header.add_widget(
                Image(
                    source=logo,
                    size_hint_x=None,
                    width=dp(48),
                )
            )

        title_scroll = ScrollView(do_scroll_x=False)

        title = WrappedLabel(
            'شرکت رادیوگرافی صنعتی ایران\n'
            'برآورد محاسبات؛ بدون تأیید ایمنی',
            color=ORANGE,
        )

        title_scroll.add_widget(title)
        header.add_widget(title_scroll)
        root.add_widget(header)

        selectors = GridLayout(
            cols=4,
            size_hint_y=None,
            height=dp(44),
            spacing=dp(4),
        )

        self.iso_buttons = {}

        for source in ISOTOPES:
            button = Button(
                text=source,
                background_normal='',
                font_size=sp(13),
                background_color=(
                    ORANGE
                    if source == self.current_source
                    else INACTIVE
                ),
            )

            button.bind(
                on_release=lambda inst, name=source:
                self.set_source(name)
            )

            self.iso_buttons[source] = button
            selectors.add_widget(button)

        root.add_widget(selectors)

        if not FONT_PATH:
            root.add_widget(
                WrappedLabel(
                    'هشدار: فونت فارسی پیدا نشد؛ '
                    'فایل Vazirmatn-Regular.ttf را کنار برنامه بگذارید.',
                    color=(1, .7, .3, 1),
                )
            )

        self.sm = ScreenManager(
            transition=FadeTransition(duration=.15)
        )

        screens = (
            (SafetyScreen, 'safety'),
            (XRayScreen, 'xray'),
            (DecayScreen, 'decay'),
            (ExposureScreen, 'exposure'),
        )

        for cls, name in screens:
            self.sm.add_widget(cls(self, name=name))

        self.sm.add_widget(
            IsotopeInfoScreen(name='info')
        )

        root.add_widget(self.sm)

        # Horizontal scrolling for narrow phone screens.
        nav_scroll = ScrollView(
            size_hint_y=None,
            height=dp(56),
            do_scroll_y=False,
        )

        nav = GridLayout(
            rows=1,
            size_hint_x=None,
            spacing=dp(2),
        )

        nav.bind(
            minimum_width=nav.setter('width')
        )

        self.nav_buttons = {}

        tabs = (
            ('مرزبندی', 'safety'),
            ('ایکس‌ری', 'xray'),
            ('واپاشی', 'decay'),
            ('پرتودهی', 'exposure'),
            ('ایزوتوپ‌ها', 'info'),
        )

        for label, name in tabs:
            button = Button(
                text=fa(label),
                size_hint_x=None,
                width=dp(100),
                background_normal='',
                font_size=sp(12),
                background_color=(
                    ORANGE if name == 'safety' else INACTIVE
                ),
                **FONT_KW,
            )

            button.bind(
                on_release=lambda inst, target=name:
                self.switch_tab(target)
            )

            self.nav_buttons[name] = button
            nav.add_widget(button)

        nav_scroll.add_widget(nav)
        root.add_widget(nav_scroll)

        return root

    def set_source(self, name):
        self.current_source = name

        for source, button in self.iso_buttons.items():
            button.background_color = (
                ORANGE if source == name else INACTIVE
            )

    def switch_tab(self, name):
        self.sm.current = name

        for target, button in self.nav_buttons.items():
            button.background_color = (
                ORANGE if target == name else INACTIVE
            )


if __name__ == '__main__':
    NDTMainApp().run()
