# -*- coding: utf-8 -*-
import logging
import os

import arabic_reshaper
from bidi.algorithm import get_display

from kivy.app import App
from kivy.core.text import Label as CoreLabel
from kivy.core.window import Window
from kivy.graphics import Color, Line, RoundedRectangle
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

from ndt_calculator import (
    ISOTOPES,
    boundary_estimate,
    decay,
    exposure_seconds,
    measured_distance,
    number,
)


BASE = os.path.dirname(os.path.abspath(__file__))

BG = (.043, .063, .137, 1)
CARD = (.082, .114, .224, 1)
EDGE = (.169, .212, .361, 1)
ACCENT = (.525, .651, 1, 1)
TEXT = (.949, .961, 1, 1)
MUTED = (.635, .675, .796, 1)
WARNING = (1, .74, .43, 1)


def asset(name):
    for folder in (BASE, os.path.join(BASE, 'assets')):
        path = os.path.join(folder, name)
        if os.path.isfile(path):
            return path
    return None


FONT = (
    asset('Vazirmatn-Regular.ttf')
    or asset('font.ttf')
    or asset('Vazir.ttf')
    or 'Roboto'
)


def fa(text):
    return get_display(
        arabic_reshaper.reshape(str(text))
    )


def fmt(value):
    return format(value, '.4g')


def rounded(widget, fill=CARD, edge=EDGE, radius=16):
    with widget.canvas.before:
        paint = Color(*fill)
        shape = RoundedRectangle(radius=[dp(radius)])
        Color(*edge)
        line = Line(width=1)

    def update(*_):
        shape.pos = widget.pos
        shape.size = widget.size
        line.rounded_rectangle = (
            *widget.pos,
            *widget.size,
            dp(radius),
        )

    widget.bind(pos=update, size=update)
    update()

    return paint


class Panel(BoxLayout):
    def __init__(self, fill=CARD, **kwargs):
        super().__init__(**kwargs)
        rounded(self, fill)


class Txt(Label):
    logical = StringProperty('')

    def __init__(self, text='', **kwargs):
        kwargs.setdefault('font_size', sp(13))
        kwargs.setdefault('color', TEXT)
        kwargs.setdefault('halign', 'right')

        super().__init__(
            text='',
            font_name=FONT,
            size_hint_y=None,
            **kwargs,
        )

        self.bind(
            width=self._wrap,
            logical=self._wrap,
            font_size=self._wrap,
            texture_size=self._fit,
        )

        self.logical = str(text)
        self._wrap()
        self._fit()

    def _wrap(self, *_):
        # Wrap logical Persian before shaping individual lines.
        width = max(dp(1), self.width)
        lines = []

        for paragraph in self.logical.split('\n'):
            line = ''

            for word in paragraph.split():
                trial = f'{line} {word}'.strip()

                probe = CoreLabel(
                    text=fa(trial),
                    font_name=self.font_name,
                    font_size=self.font_size,
                    bold=self.bold,
                )
                probe.refresh()

                if line and probe.texture.size[0] > width:
                    lines.append(fa(line))
                    line = word
                else:
                    line = trial

            lines.append(fa(line))

        self.text_size = (width, None)
        self.text = '\n'.join(lines)

    def _fit(self, *_):
        self.height = max(
            dp(24),
            self.texture_size[1] + dp(8),
        )


class Action(Button):
    def __init__(self, text, active=False, **kwargs):
        super().__init__(
            text=fa(text),
            font_name=FONT,
            font_size=sp(12),
            background_normal='',
            background_down='',
            background_color=(0, 0, 0, 0),
            **kwargs,
        )

        self.paint = rounded(self)
        self.set_active(active)

        self.bind(size=self._wrap)
        self._wrap()

    def _wrap(self, *_):
        self.text_size = (
            max(dp(1), self.width - dp(6)),
            None,
        )
        self.halign = 'center'

    def set_active(self, active):
        self.paint.rgba = ACCENT if active else CARD
        self.color = BG if active else MUTED


class Field(Panel):
    def __init__(self, title, unit, default='', **kwargs):
        super().__init__(
            orientation='vertical',
            padding=dp(10),
            spacing=dp(2),
            size_hint_y=None,
            height=dp(116),
            **kwargs,
        )

        self.add_widget(
            Txt(
                title,
                font_size=sp(12),
                color=MUTED,
            )
        )

        self.input = TextInput(
            text=default,
            multiline=False,
            write_tab=False,
            font_name=FONT,
            font_size=sp(23),
            halign='right',
            background_normal='',
            background_active='',
            background_color=(0, 0, 0, 0),
            foreground_color=TEXT,
            cursor_color=ACCENT,
            padding=[0, dp(3)],
            size_hint_y=None,
            height=dp(39),
        )
        self.add_widget(self.input)

        self.add_widget(
            Txt(
                unit,
                halign='left',
                color=MUTED,
                font_size=sp(11),
            )
        )


TITLES = {
    'gamma': 'مرزبندی و حفاظ',
    'xray': 'ایکس‌ری؛ نرخ دوز مرجع',
    'decay': 'واپاشی چشمه',
    'exposure': 'زمان پرتودهی',
}


class CalculatorScreen(Screen):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)

        self.app = app
        self.mode = 'model'
        self.ready = False

        self.inputs = {}
        self.titles = {}
        self.iso_buttons = {}

        scroll = ScrollView(do_scroll_x=False)

        self.body = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=dp(12),
            padding=[0, dp(4), 0, dp(16)],
        )
        self.body.bind(
            minimum_height=self.body.setter('height')
        )

        scroll.add_widget(self.body)
        self.add_widget(scroll)

        app.bind(current_source=self.source_changed)
        self.build_form()

    def build_form(self):
        self.ready = False
        self.body.clear_widgets()

        self.inputs = {}
        self.titles = {}
        self.iso_buttons = {}

        self.body.add_widget(
            Txt(
                TITLES[self.name],
                font_size=sp(23),
                bold=True,
            )
        )

        if self.name == 'gamma':
            modes = GridLayout(
                cols=2,
                size_hint_y=None,
                height=dp(42),
                spacing=dp(8),
            )

            for key, text in (
                ('model', 'مدل ساده گاما'),
                ('measured', 'نرخ دوز مرجع'),
            ):
                button = Action(
                    text,
                    active=self.mode == key,
                )
                button.bind(
                    on_release=lambda _, k=key: self.change_mode(k)
                )
                modes.add_widget(button)

            self.body.add_widget(modes)

        needs_isotope = (
            self.name in ('decay', 'exposure')
            or (
                self.name == 'gamma'
                and self.mode == 'model'
            )
        )

        if needs_isotope:
            self.body.add_widget(
                Txt('انتخاب ایزوتوپ', color=MUTED)
            )

            selectors = GridLayout(
                cols=4,
                spacing=dp(6),
                size_hint_y=None,
                height=dp(42),
            )

            for source in ISOTOPES:
                button = Action(
                    source,
                    active=source == self.app.current_source,
                )
                button.bind(
                    on_release=lambda _, s=source: self.app.set_source(s)
                )

                self.iso_buttons[source] = button
                selectors.add_widget(button)

            self.body.add_widget(selectors)

        if self.name == 'gamma' and self.mode == 'model':
            self.add_fields([
                ('activity', 'اکتیویته', 'Ci', '40'),
                ('target', 'نرخ دوز هدف', 'µSv/h', '2.5'),
            ])
            self.add_fields([
                (
                    'lead',
                    'ضخامت سرب در مسیر پرتو',
                    'mm',
                    '0',
                ),
            ], cols=1)

        elif self.name in ('gamma', 'xray'):
            self.add_fields([
                ('rate', 'نرخ دوز مرجع', 'µSv/h', ''),
                ('distance', 'فاصله اندازه‌گیری', 'm', ''),
            ])
            self.add_fields([
                ('target', 'نرخ دوز هدف', 'µSv/h', ''),
            ], cols=1)

        elif self.name == 'decay':
            self.add_fields([
                ('initial', 'اکتیویته اولیه', 'Ci', '80'),
                ('days', 'روزهای سپری‌شده', 'day', '30'),
            ])

        else:
            self.add_fields([
                ('time', 'زمان مرجع تأییدشده', 's', ''),
            ], cols=1)

            self.add_fields([
                ('ref_activity', 'اکتیویته مرجع', 'Ci', ''),
                ('ref_sfd', 'SFD مرجع', 'cm', ''),
                ('activity', 'اکتیویته فعلی', 'Ci', ''),
                ('sfd', 'SFD جدید', 'cm', ''),
            ])

        result = Panel(
            orientation='vertical',
            fill=(.125, .18, .341, 1),
            padding=dp(16),
            spacing=dp(8),
            size_hint_y=None,
        )
        result.bind(
            minimum_height=result.setter('height')
        )

        self.result_title = Txt(
            'نتیجه محاسبه',
            color=ACCENT,
            font_size=sp(14),
        )
        self.result_value = Txt(
            '—',
            halign='center',
            font_size=sp(32),
            bold=True,
        )
        self.result_detail = Txt(
            '',
            halign='center',
            color=MUTED,
        )

        for widget in (
            self.result_title,
            self.result_value,
            self.result_detail,
        ):
            result.add_widget(widget)

        self.body.add_widget(result)

        if self.name in ('gamma', 'xray'):
            self.body.add_widget(
                Txt(
                    'برآورد مدل؛ نه تأیید ایمنی',
                    color=WARNING,
                    halign='center',
                    font_size=sp(12),
                )
            )

        about = Action(
            'درباره محاسبات و محدودیت‌ها',
            size_hint_y=None,
            height=dp(46),
        )
        about.bind(
            on_release=lambda _: self.app.switch_tab('info')
        )
        self.body.add_widget(about)

        if FONT == 'Roboto':
            self.body.add_widget(
                Txt(
                    'Missing font: add font.ttf',
                    color=WARNING,
                )
            )

        self.ready = True
        self.calc()

    def add_fields(self, specs, cols=2):
        grid = GridLayout(
            cols=cols,
            spacing=dp(10),
            size_hint_y=None,
        )
        grid.bind(
            minimum_height=grid.setter('height')
        )

        for key, title, unit, default in specs:
            field = Field(title, unit, default)

            self.inputs[key] = field.input
            self.titles[key] = title

            field.input.bind(text=self.calc)
            grid.add_widget(field)

        self.body.add_widget(grid)

    def change_mode(self, mode):
        if self.mode != mode:
            self.mode = mode
            self.build_form()

    def source_changed(self, *_):
        for source, button in self.iso_buttons.items():
            button.set_active(
                source == self.app.current_source
            )

        if self.name == 'exposure':
            for key in (
                'time',
                'ref_activity',
                'ref_sfd',
            ):
                self.inputs[key].text = ''

        self.calc()

    def value(self, key, positive=False):
        return number(
            self.inputs[key].text,
            self.titles[key],
            positive,
        )

    def calc(self, *_):
        if not self.ready:
            return

        # Clear the previous result before validating new input.
        self.result_value.logical = '—'
        self.result_detail.logical = ''
        self.result_value.color = TEXT
        self.result_title.logical = 'نتیجه محاسبه'

        if any(
            not entry.text.strip()
            for entry in self.inputs.values()
        ):
            self.result_detail.logical = (
                'همه ورودی‌ها را تکمیل کنید'
            )
            return

        try:
            title, value, detail = self.compute()

            self.result_title.logical = title
            self.result_value.logical = value
            self.result_detail.logical = detail

        except ValueError as exc:
            self.result_value.color = WARNING
            self.result_detail.logical = str(exc)

        except Exception:
            logging.exception(
                'Calculation failed: %s',
                self.name,
            )
            self.result_value.color = WARNING
            self.result_detail.logical = (
                'خطای داخلی؛ گزارش برنامه را بررسی کنید'
            )

    def compute(self):
        if self.name == 'gamma' and self.mode == 'model':
            distance, transmission = boundary_estimate(
                self.app.current_source,
                self.value('activity'),
                self.value('target', True),
                self.value('lead'),
            )

            return (
                'فاصله برآوردی مدل',
                f'{fmt(distance)} متر',
                f'ضریب عبور مدل سرب: {fmt(transmission)}',
            )

        if self.name in ('gamma', 'xray'):
            distance = measured_distance(
                self.value('rate', True),
                self.value('distance', True),
                self.value('target', True),
            )

            return (
                'فاصله برآوردی از مرجع',
                f'{fmt(distance)} متر',
                'قانون عکس مجذور؛ فقط با شرایط یکسان',
            )

        if self.name == 'decay':
            initial = self.value('initial')

            activity, percent = decay(
                self.app.current_source,
                initial,
                self.value('days'),
            )

            if initial:
                detail = f'افت اکتیویته: {fmt(percent)}٪'
            else:
                detail = (
                    'درصد افت برای اکتیویته اولیه صفر تعریف نمی‌شود'
                )

            return (
                'اکتیویته باقی‌مانده',
                f'{fmt(activity)} Ci',
                detail,
            )

        seconds = exposure_seconds(
            self.value('time', True),
            self.value('ref_activity', True),
            self.value('ref_sfd', True),
            self.value('activity', True),
            self.value('sfd', True),
        )

        return (
            'زمان مقیاس‌شده از مرجع',
            f'{fmt(seconds)} ثانیه',
            'همان ایزوتوپ، قطعه، فیلم و شرایط ظهور',
        )


NOTES = [
    (
        'کاربرد و محدودیت',
        'این برنامه ابزار برآورد است، نه تأیید ایمنی یا طراحی حفاظ.\n'
        'مرزبندی عملی نیازمند طرح مصوب، مسئول حفاظت پرتویی و '
        'اندازه‌گیری میدانی با دستگاه مناسب و کالیبره است. '
        'نرخ دوز هدف را از طرح مصوب وارد کنید؛ '
        'مقدار پیش‌فرض، حد قانونی یا پیشنهاد عملی نیست.',
    ),
    (
        'مدل ساده گاما و سرب',
        'ثابت‌های گاما و HVL از نسخه اولیه منتقل شده‌اند '
        'و مستقلاً تأیید نشده‌اند.\n'
        'تبدیل R به µSv با ضریب تقریبی 10000 انجام می‌شود؛ '
        'کمیت‌های دوز یکسان نیستند.\n'
        'تضعیف سرب مدل نمایی ساده است؛ buildup، پراکندگی، '
        'نشتی و هندسه واقعی لحاظ نشده‌اند. '
        'ضخامت بدنه کولیماتور را نمی‌توان برای دهانه خروج پرتو اعمال کرد.',
    ),
    (
        'محاسبه از نرخ دوز مرجع؛ گاما و ایکس‌ری',
        'نرخ دوز در فاصله مرجع باید واقعاً اندازه‌گیری شده باشد.\n'
        'شرایط چشمه یا دستگاه، جهت، حفاظ و هندسه باید یکسان بماند. '
        'برای ایکس‌ری، kV، جریان و فیلتراسیون نیز ثابت باشند '
        'و ابزار برای نوع پرتو مناسب باشد.\n'
        'قانون عکس مجذور در حضور پراکندگی، منابع گسترده '
        'یا میدان نزدیک الزاماً معتبر نیست.',
    ),
    (
        'واپاشی',
        'روزهای سپری‌شده را از تاریخ مرجع گواهی چشمه وارد کنید. '
        'اکتیویته مرجع و نیمه‌عمر باید با گواهی و مرجع معتبر '
        'تطبیق داده شوند. عدم‌قطعیت گواهی در خروجی محاسبه نمی‌شود.',
    ),
    (
        'زمان پرتودهی',
        'زمان فقط از اکسپوژر مرجع تأییدشده مقیاس می‌شود. '
        'ایزوتوپ، جنس، ضخامت، فیلم، اسکرین، دانسیته هدف '
        'و ظهور باید همان باشند.\n'
        'فاصله‌های SFD باید هر دو با یک واحد وارد شوند. '
        'با تغییر ایزوتوپ، ورودی‌های مرجع پاک می‌شوند. '
        'این نتیجه تضمین کیفیت فیلم نیست.',
    ),
]


class InfoScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        scroll = ScrollView(do_scroll_x=False)

        body = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=dp(12),
            padding=[0, dp(4), 0, dp(16)],
        )
        body.bind(
            minimum_height=body.setter('height')
        )

        body.add_widget(
            Txt(
                'درباره محاسبات',
                font_size=sp(23),
                bold=True,
            )
        )

        for title, text in NOTES:
            self.card(body, title, text)

        for source, data in ISOTOPES.items():
            self.card(
                body,
                f"{data['name']} — {source}",
                f"نیمه‌عمر ورودی: {data['half_life']} روز\n"
                f"ثابت گامای ورودی: {data['gamma']} R·m²/(Ci·h)\n"
                f"HVL سرب: {data['hvl_pb']} mm\n"
                f"HVL فولاد: {data['hvl_fe']} mm\n"
                'داده‌های قدیمی؛ برای طراحی حفاظ تأیید نشده‌اند.',
            )

        scroll.add_widget(body)
        self.add_widget(scroll)

    @staticmethod
    def card(body, title, text):
        panel = Panel(
            orientation='vertical',
            padding=dp(14),
            spacing=dp(6),
            size_hint_y=None,
        )
        panel.bind(
            minimum_height=panel.setter('height')
        )

        panel.add_widget(
            Txt(
                title,
                color=ACCENT,
                bold=True,
                font_size=sp(15),
            )
        )
        panel.add_widget(
            Txt(text, color=MUTED)
        )

        body.add_widget(panel)


class NDTMainApp(App):
    current_source = StringProperty('Ir-192')

    def build(self):
        self.title = 'NDT — Radiography'
        Window.clearcolor = BG
        Window.softinput_mode = 'below_target'

        root = BoxLayout(
            orientation='vertical',
            padding=dp(12),
            spacing=dp(12),
        )

        header = Panel(
            size_hint_y=None,
            height=dp(72),
            padding=dp(10),
            spacing=dp(12),
        )

        logo = asset('logo.png')

        if logo:
            header.add_widget(
                Image(
                    source=logo,
                    size_hint_x=None,
                    width=dp(94),
                )
            )
        else:
            header.add_widget(
                Txt(
                    'N.D.T\nI.I.R.Co.',
                    halign='center',
                    color=ACCENT,
                    size_hint_x=None,
                    width=dp(94),
                )
            )

        header.add_widget(
            Label(
                text=fa('دستیار رادیوگرافی'),
                font_name=FONT,
                font_size=sp(17),
                color=TEXT,
            )
        )
        root.add_widget(header)

        self.sm = ScreenManager(
            transition=FadeTransition(duration=.12)
        )

        for name in TITLES:
            self.sm.add_widget(
                CalculatorScreen(self, name=name)
            )

        self.sm.add_widget(
            InfoScreen(name='info')
        )
        root.add_widget(self.sm)

        scroll = ScrollView(
            size_hint_y=None,
            height=dp(58),
            do_scroll_y=False,
            bar_width=0,
        )

        nav = GridLayout(
            rows=1,
            size_hint_x=None,
            spacing=dp(5),
        )

        scroll.bind(
            width=lambda _, width: setattr(
                nav,
                'width',
                max(width, dp(330)),
            )
        )

        self.nav_buttons = {}

        for name, title in (
            ('gamma', 'مرزبندی'),
            ('xray', 'ایکس‌ری'),
            ('decay', 'واپاشی'),
            ('exposure', 'پرتودهی'),
            ('info', 'اطلاعات'),
        ):
            button = Action(
                title,
                active=name == 'gamma',
            )
            button.bind(
                on_release=lambda _, n=name: self.switch_tab(n)
            )

            self.nav_buttons[name] = button
            nav.add_widget(button)

        scroll.add_widget(nav)
        root.add_widget(scroll)

        Window.bind(on_keyboard=self.on_keyboard)

        return root

    def set_source(self, source):
        if source in ISOTOPES:
            self.current_source = source

    def switch_tab(self, name):
        self.sm.current = name

        for target, button in self.nav_buttons.items():
            button.set_active(target == name)

    def on_keyboard(self, window, key, *_):
        if key == 27:
            for screen in self.sm.screens:
                for entry in getattr(
                    screen,
                    'inputs',
                    {},
                ).values():
                    if entry.focus:
                        entry.focus = False
                        return True

            if self.sm.current != 'gamma':
                self.switch_tab('gamma')
                return True

        return False


if __name__ == '__main__':
    NDTMainApp().run()
