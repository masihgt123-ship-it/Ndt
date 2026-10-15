# -*- coding: utf-8 -*-
import math
import os
import arabic_reshaper
from bidi.algorithm import get_display

from kivy.app import App
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.graphics import Color, RoundedRectangle, Rectangle

# پس‌زمینه دارک متالیک
Window.clearcolor = (0.07, 0.08, 0.09, 1.0)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_asset_path(filename):
    """بررسی و لود ایمن فایل‌ها"""
    for p in [os.path.join(BASE_DIR, filename), os.path.join(BASE_DIR, 'assets', filename), filename]:
        if os.path.isfile(p):
            return p
    return None

# تشخیص ایمن فونت فارسی
FONT_FILE = get_asset_path('font.ttf') or get_asset_path('Vazirmatn-Regular.ttf')

def fa(text):
    """آماده‌سازی متن فارسی برای نمایش درست از راست به چپ"""
    if not text:
        return ""
    try:
        reshaped = arabic_reshaper.reshape(str(text))
        return get_display(reshaped)
    except Exception:
        return str(text)

# داده‌های مهندسی ایزوتوپ‌ها
ISOTOPES = {
    'Ir-192': {'gamma': 0.48, 'hvl_pb': 4.8, 'hvl_fe': 12.5, 'factor': 1.0},
    'Se-75':  {'gamma': 0.20, 'hvl_pb': 2.0, 'hvl_fe': 8.0,  'factor': 0.85},
    'Co-60':  {'gamma': 1.32, 'hvl_pb': 12.5,'hvl_fe': 21.0, 'factor': 2.1},
    'Cs-137': {'gamma': 0.33, 'hvl_pb': 6.5, 'hvl_fe': 16.0, 'factor': 1.2}
}

class SafeCard(BoxLayout):
    """کارت زیبا بدون باگ رسم گرافیکی"""
    def __init__(self, bg_color=(0.12, 0.14, 0.16, 0.95), radius=10, **kwargs):
        super(SafeCard, self).__init__(**kwargs)
        self.bg_color = bg_color
        self.radius = radius
        with self.canvas.before:
            Color(*self.bg_color)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[self.radius])
        self.bind(pos=self._update_shape, size=self._update_shape)

    def _update_shape(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

class SafeInput(TextInput):
    """ورودی متن شیک و پایدار برای اندروید"""
    def __init__(self, **kwargs):
        super(SafeInput, self).__init__(**kwargs)
        self.background_normal = ''
        self.background_active = ''
        self.background_color = (0.05, 0.06, 0.07, 1.0)
        self.foreground_color = (1.0, 0.80, 0.20, 1.0)
        self.cursor_color = (1.0, 0.45, 0.0, 1.0)
        self.font_size = sp(15)
        self.multiline = False
        self.halign = 'center'
        self.padding = [dp(6), dp(8), dp(6), dp(8)]

class NDTMainApp(App):
    def build(self):
        self.title = 'رادیوگرافی صنعتی'
        self.current_source = 'Ir-192'
        self.source_buttons = {}

        root = FloatLayout()

        # تصویر پس‌زمینه
        bg_file = get_asset_path('bg.png')
        if bg_file:
            with root.canvas.before:
                self.bg_rect = Rectangle(source=bg_file, pos=root.pos, size=root.size)
                Color(0.04, 0.05, 0.06, 0.88)
                self.bg_overlay = Rectangle(pos=root.pos, size=root.size)
            root.bind(pos=self._sync_bg, size=self._sync_bg)

        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        content = BoxLayout(orientation='vertical', size_hint_y=None, padding=dp(10), spacing=dp(8))
        content.bind(minimum_height=content.setter('height'))

        # بنر بالای صفحه
        banner = SafeCard(size_hint_y=None, height=dp(68), padding=dp(6), spacing=dp(8))
        logo_f = get_asset_path('logo.png')
        if logo_f:
            banner.add_widget(Image(source=logo_f, size_hint=(None, 1), width=dp(50)))
        
        t_box = BoxLayout(orientation='vertical')
        kw = {'font_name': FONT_FILE} if FONT_FILE else {}
        t_box.add_widget(Label(text=fa('شرکت رادیوگرافی صنعتی ایران'), font_size=sp(14), bold=True, color=(1.0, 0.50, 0.0, 1.0), **kw))
        t_box.add_widget(Label(text=fa('محاسبات دوز، فاصله ایمن و پرتوگیری'), font_size=sp(10), color=(0.7, 0.75, 0.8, 1.0), **kw))
        banner.add_widget(t_box)
        content.add_widget(banner)

        # تب‌های انتخاب منبع پرتو (گاما + پرتو ایکس)
        tab_box = SafeCard(orientation='vertical', size_hint_y=None, height=dp(75), padding=dp(6), spacing=dp(4))
        tab_box.add_widget(Label(text=fa('انتخاب منبع پرتو:'), font_size=sp(11), color=(0.8, 0.8, 0.8, 1.0), size_hint_y=None, height=dp(18), **kw))
        
        grid_tabs = GridLayout(cols=5, spacing=dp(4), size_hint_y=None, height=dp(40))
        for s in ['Ir-192', 'Se-75', 'Co-60', 'Cs-137', 'X-Ray']:
            btn = Button(
                text=s,
                bold=True,
                font_size=sp(11),
                background_normal='',
                background_color=(1.0, 0.45, 0.0, 1.0) if s == self.current_source else (0.18, 0.20, 0.22, 1.0),
                color=(1, 1, 1, 1)
            )
            btn.bind(on_release=lambda inst, name=s: self.change_source(name))
            self.source_buttons[s] = btn
            grid_tabs.add_widget(btn)
        tab_box.add_widget(grid_tabs)
        content.add_widget(tab_box)

        # کارت ورودی‌ها
        inp_box = SafeCard(orientation='vertical', size_hint_y=None, height=dp(210), padding=dp(8), spacing=dp(6))
        grid_inps = GridLayout(cols=2, spacing=dp(8), size_hint_y=1)

        self.in1 = SafeInput(text='50')
        self.lbl1 = Label(text=fa('اکتیویته چشمه (Ci):'), font_size=sp(11), color=(0.9, 0.9, 0.9, 1.0), **kw)
        grid_inps.add_widget(self.in1)
        grid_inps.add_widget(self.lbl1)

        self.in2 = SafeInput(text='0')
        self.lbl2 = Label(text=fa('شیلد سرب کولیماتور (mm):'), font_size=sp(11), color=(0.9, 0.9, 0.9, 1.0), **kw)
        grid_inps.add_widget(self.in2)
        grid_inps.add_widget(self.lbl2)

        self.in_thick = SafeInput(text='10')
        grid_inps.add_widget(self.in_thick)
        grid_inps.add_widget(Label(text=fa('ضخامت قطعه (mm):'), font_size=sp(11), color=(0.9, 0.9, 0.9, 1.0), **kw))

        self.in_sfd = SafeInput(text='60')
        grid_inps.add_widget(self.in_sfd)
        grid_inps.add_widget(Label(text=fa('فاصله SFD (cm):'), font_size=sp(11), color=(0.9, 0.9, 0.9, 1.0), **kw))

        inp_box.add_widget(grid_inps)
        content.add_widget(inp_box)

        # دکمه محاسبه
        btn_calc = Button(
            text=fa('محاسبه فاصله ایمن و زمان اکسپوژر'),
            bold=True,
            font_size=sp(14),
            size_hint_y=None,
            height=dp(46),
            background_normal='',
            background_color=(1.0, 0.45, 0.0, 1.0),
            color=(1, 1, 1, 1),
            **kw
        )
        btn_calc.bind(on_release=self.calculate)
        content.add_widget(btn_calc)

        # کارت نمایش خروجی
        self.res_card = SafeCard(
            orientation='vertical',
            bg_color=(0.10, 0.12, 0.14, 0.98),
            size_hint_y=None,
            height=dp(150),
            padding=dp(8),
            spacing=dp(5)
        )
        self.res_dist = Label(text=fa('شعاع طناب‌کشی ایمن: -- متر'), font_size=sp(14), bold=True, color=(0.2, 1.0, 0.5, 1.0), **kw)
        self.res_op = Label(text=fa('موقعیت مجاز اپراتور: -- متر'), font_size=sp(12), color=(0.8, 0.85, 0.9, 1.0), **kw)
        self.res_time = Label(text=fa('زمان تخمینی اکسپوژر: -- ثانیه'), font_size=sp(13), bold=True, color=(1.0, 0.8, 0.2, 1.0), **kw)

        self.res_card.add_widget(Label(text=fa('نتایج محاسبات مهندسی:'), font_size=sp(12), bold=True, color=(1.0, 0.6, 0.1, 1.0), **kw))
        self.res_card.add_widget(self.res_dist)
        self.res_card.add_widget(self.res_op)
        self.res_card.add_widget(self.res_time)
        content.add_widget(self.res_card)

        # فوتر
        content.add_widget(Label(text=fa('تلفن تماس: 09122012248 - 09121042253'), font_size=sp(10), color=(0.5, 0.55, 0.6, 1.0), size_hint_y=None, height=dp(20), **kw))

        scroll.add_widget(content)
        root.add_widget(scroll)
        return root

    def _sync_bg(self, *args):
        if hasattr(self, 'bg_rect'):
            self.bg_rect.pos = Window.pos
            self.bg_rect.size = Window.size
            self.bg_overlay.pos = Window.pos
            self.bg_overlay.size = Window.size

    def change_source(self, name):
        self.current_source = name
        for s, b in self.source_buttons.items():
            b.background_color = (1.0, 0.45, 0.0, 1.0) if s == name else (0.18, 0.20, 0.22, 1.0)
        
        if name == 'X-Ray':
            self.lbl1.text = fa('ولتاژ تیوب (kV):')
            self.in1.text = '200'
            self.lbl2.text = fa('جریان تیوب (mA):')
            self.in2.text = '4.0'
        else:
            self.lbl1.text = fa('اکتیویته چشمه (Ci):')
            self.in1.text = '45'
            self.lbl2.text = fa('شیلد سرب کولیماتور (mm):')
            self.in2.text = '0'

    def calculate(self, *args):
        try:
            v1 = float(self.in1.text.strip() or '0')
            v2 = float(self.in2.text.strip() or '0')
            thick = float(self.in_thick.text.strip() or '10')
            sfd = float(self.in_sfd.text.strip() or '60')

            dist_factor = math.pow(max(10.0, sfd) / 50.0, 2.0)

            if self.current_source == 'X-Ray':
                kv = max(50.0, v1)
                ma = max(0.5, v2)
                # دوز خروجی دستگاه X-Ray
                output_rate = math.pow(kv / 100.0, 2.4) * 0.14 * ma * 60.0 * 10000.0
                safe_d = math.sqrt(max(0.1, output_rate) / 7.5)
                # زمان تابش
                hvl_fe = 4.0 + (kv / 50.0)
                thick_factor = math.pow(2.0, max(0.0, thick) / hvl_fe)
                sec = (45.0 * thick_factor * dist_factor) / (ma * (kv / 150.0))
            else:
                curie = max(0.01, v1)
                shield = max(0.0, v2)
                iso = ISOTOPES[self.current_source]
                trans = math.pow(2.0, -(shield / iso['hvl_pb'])) if iso['hvl_pb'] > 0 else 1.0
                dose_rate_1m = iso['gamma'] * curie * 10000.0 * trans
                safe_d = math.sqrt(max(0.1, dose_rate_1m) / 7.5)
                # زمان تابش
                thick_factor = math.pow(2.0, max(0.0, thick) / iso['hvl_fe'])
                sec = (iso['factor'] * thick_factor * dist_factor * 120.0) / (curie / 10.0)

            safe_d = round(safe_d, 2)
            op_d = round(safe_d * 1.25, 2)
            sec = round(max(1.0, sec), 1)

            m = int(sec // 60)
            s = int(sec % 60)
            t_txt = f"{sec} ثانیه" if m == 0 else f"{m} دقیقه و {s} ثانیه"

            self.res_dist.text = fa(f'شعاع طناب‌کشی ایمن: {safe_d} متر')
            self.res_op.text = fa(f'موقعیت مجاز اپراتور: {op_d} متر')
            self.res_time.text = fa(f'زمان تخمینی اکسپوژر: {t_txt}')

        except Exception:
            self.res_dist.text = fa('خطا در ارقام ورودی!')
            self.res_op.text = fa('لطفاً اعداد را به انگلیسی و صحیح بزنید')
            self.res_time.text = fa('')

if __name__ == '__main__':
    NDTMainApp().run()
