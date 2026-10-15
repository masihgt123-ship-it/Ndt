# -*- coding: utf-8 -*-
import os
import math

import arabic_reshaper
from bidi.algorithm import get_display

from kivy.app import App
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.graphics import Color, RoundedRectangle, Rectangle

Window.clearcolor = (0.07, 0.08, 0.10, 1.0)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_asset(filename):
    for p in [os.path.join(BASE_DIR, filename), os.path.join(BASE_DIR, 'assets', filename), filename]:
        if os.path.isfile(p):
            return p
    return None

FONT_PATH = get_asset('Vazirmatn-Regular.ttf') or get_asset('font.ttf')

def fa(text):
    if not text:
        return ""
    try:
        return get_display(arabic_reshaper.reshape(str(text)))
    except Exception:
        return str(text)

ISOTOPES = {
    'Ir-192': {'gamma': 0.48, 'hvl_pb': 4.8, 'hvl_fe': 12.5, 'factor': 1.0},
    'Se-75':  {'gamma': 0.20, 'hvl_pb': 2.0, 'hvl_fe': 8.0,  'factor': 0.85},
    'Co-60':  {'gamma': 1.32, 'hvl_pb': 12.5,'hvl_fe': 21.0, 'factor': 2.1},
    'Cs-137': {'gamma': 0.33, 'hvl_pb': 6.5, 'hvl_fe': 16.0, 'factor': 1.2}
}

class SafeCard(BoxLayout):
    def __init__(self, bg_color=(0.13, 0.15, 0.18, 0.96), radius=8, **kwargs):
        super(SafeCard, self).__init__(**kwargs)
        with self.canvas.before:
            Color(*bg_color)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[radius])
        self.bind(pos=self._up, size=self._up)
    def _up(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

class SafeInput(TextInput):
    def __init__(self, **kwargs):
        super(SafeInput, self).__init__(**kwargs)
        self.background_normal = ''
        self.background_active = ''
        self.background_color = (0.05, 0.06, 0.08, 1.0)
        self.foreground_color = (1.0, 0.82, 0.20, 1.0)
        self.cursor_color = (1.0, 0.48, 0.0, 1.0)
        self.font_size = sp(15)
        self.multiline = False
        self.halign = 'center'
        self.padding = [dp(6), dp(8), dp(6), dp(8)]

class NDTMainApp(App):
    def build(self):
        self.title = 'رادیوگرافی صنعتی'
        self.current_source = 'Ir-192'
        self.source_buttons = {}
        self.bottom_buttons = {}

        root = BoxLayout(orientation='vertical')

        bg_file = get_asset('bg.png')
        if bg_file:
            try:
                with root.canvas.before:
                    self.bg_rect = Rectangle(source=bg_file, pos=root.pos, size=root.size)
                    Color(0.04, 0.05, 0.06, 0.88)
                    self.bg_overlay = Rectangle(pos=root.pos, size=root.size)
                root.bind(pos=self._sync_bg, size=self._sync_bg)
            except Exception:
                pass

        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        content = BoxLayout(orientation='vertical', size_hint_y=None, padding=dp(10), spacing=dp(8))
        content.bind(minimum_height=content.setter('height'))

        font_kw = {'font_name': FONT_PATH} if FONT_PATH and os.path.exists(FONT_PATH) else {}

        # ۱. بنر و هدر بالا
        banner = SafeCard(size_hint_y=None, height=dp(68), padding=[dp(10), dp(6), dp(12), dp(6)], spacing=dp(10))
        logo_f = get_asset('logo.png')
        if logo_f:
            banner.add_widget(Image(source=logo_f, size_hint=(None, 1), width=dp(52)))
        
        t_box = BoxLayout(orientation='vertical', padding=[dp(4), 0, 0, 0])
        t_box.add_widget(Label(text=fa('شرکت رادیوگرافی صنعتی ایران'), font_size=sp(13), bold=True, color=(1.0, 0.50, 0.0, 1.0), halign='right', **font_kw))
        t_box.add_widget(Label(text=fa('محاسبات دوز، فاصله ایمن و پرتوگیری'), font_size=sp(10), color=(0.75, 0.80, 0.85, 1.0), halign='right', **font_kw))
        banner.add_widget(t_box)
        content.add_widget(banner)

        # ۲. تب‌های انتخاب ایزوتوپ (بالا)
        tab_card = SafeCard(orientation='vertical', size_hint_y=None, height=dp(72), padding=dp(6), spacing=dp(4))
        tab_card.add_widget(Label(text=fa('انتخاب ایزوتوپ:'), font_size=sp(11), color=(0.85, 0.85, 0.85, 1.0), size_hint_y=None, height=dp(18), **font_kw))
        
        grid_tabs = GridLayout(cols=4, spacing=dp(6), size_hint_y=None, height=dp(38))
        for s in ['Ir-192', 'Se-75', 'Co-60', 'Cs-137']:
            btn = Button(
                text=s,
                bold=True,
                font_size=sp(12),
                background_normal='',
                background_color=(1.0, 0.45, 0.0, 1.0) if s == self.current_source else (0.20, 0.22, 0.25, 1.0),
                color=(1, 1, 1, 1),
                **font_kw
            )
            btn.bind(on_release=lambda inst, name=s: self.change_source(name))
            self.source_buttons[s] = btn
            grid_tabs.add_widget(btn)
        tab_card.add_widget(grid_tabs)
        content.add_widget(tab_card)

        # ۳. کارت ورودی‌ها
        inp_box = SafeCard(orientation='vertical', size_hint_y=None, height=dp(215), padding=dp(8), spacing=dp(6))
        grid_inps = GridLayout(cols=2, spacing=dp(8), size_hint_y=1)

        self.in1 = SafeInput(text='50')
        self.lbl1 = Label(text=fa('اکتیویته چشمه (Ci):'), font_size=sp(11), color=(0.9, 0.9, 0.9, 1.0), **font_kw)
        grid_inps.add_widget(self.in1)
        grid_inps.add_widget(self.lbl1)

        self.in2 = SafeInput(text='0')
        self.lbl2 = Label(text=fa('شیلد سرب کولیماتور (mm):'), font_size=sp(11), color=(0.9, 0.9, 0.9, 1.0), **font_kw)
        grid_inps.add_widget(self.in2)
        grid_inps.add_widget(self.lbl2)

        self.in_thick = SafeInput(text='10')
        grid_inps.add_widget(self.in_thick)
        grid_inps.add_widget(Label(text=fa('ضخامت قطعه فولادی (mm):'), font_size=sp(11), color=(0.9, 0.9, 0.9, 1.0), **font_kw))

        self.in_sfd = SafeInput(text='60')
        grid_inps.add_widget(self.in_sfd)
        grid_inps.add_widget(Label(text=fa('فاصله منبع تا فیلم SFD (cm):'), font_size=sp(11), color=(0.9, 0.9, 0.9, 1.0), **font_kw))

        inp_box.add_widget(grid_inps)
        content.add_widget(inp_box)

        # دکمه محاسبه
        btn_calc = Button(
            text=fa('محاسبه فاصله ایمن و زمان پرتوگیری'),
            bold=True,
            font_size=sp(13),
            size_hint_y=None,
            height=dp(45),
            background_normal='',
            background_color=(1.0, 0.45, 0.0, 1.0),
            color=(1, 1, 1, 1),
            **font_kw
        )
        btn_calc.bind(on_release=self.calculate)
        content.add_widget(btn_calc)

        # ۴. کارت نمایش خروجی
        self.res_card = SafeCard(
            orientation='vertical',
            bg_color=(0.10, 0.12, 0.15, 0.98),
            size_hint_y=None,
            height=dp(140),
            padding=dp(8),
            spacing=dp(4)
        )
        self.res_dist = Label(text=fa('شعاع فاصله طناب‌کشی ایمن: -- متر'), font_size=sp(13), bold=True, color=(0.2, 1.0, 0.5, 1.0), **font_kw)
        self.res_info = Label(text=fa('اطلاعات منبع و تضعیف: --'), font_size=sp(11), color=(0.8, 0.85, 0.9, 1.0), **font_kw)
        self.res_op = Label(text=fa('استقرار مجاز اپراتور: -- متر'), font_size=sp(12), color=(1.0, 0.82, 0.2, 1.0), **font_kw)

        self.res_card.add_widget(self.res_dist)
        self.res_card.add_widget(self.res_info)
        self.res_card.add_widget(self.res_op)
        content.add_widget(self.res_card)

        # فوتر تماس
        content.add_widget(Label(text=fa('تلفن تماس: 09122012248 - 09121042253'), font_size=sp(10), color=(0.55, 0.60, 0.65, 1.0), size_hint_y=None, height=dp(20), **font_kw))

        scroll.add_widget(content)
        root.add_widget(scroll)

        # ۵. نوار ناوبری پایین صفحه (۵ دکمه شامل X-Ray)
        nav_bar = GridLayout(cols=5, size_hint_y=None, height=dp(52))
        bottom_tabs = ['مرزبندی و حفاظ', 'ایکس‌ری (X-Ray)', 'واپاشی روز', 'زمان پرتودهی', 'شناسنامه ایزوتوپ']
        
        for i, t_name in enumerate(bottom_tabs):
            is_active = (i == 0)
            b = Button(
                text=fa(t_name),
                font_size=sp(10),
                bold=True,
                background_normal='',
                background_color=(1.0, 0.45, 0.0, 1.0) if is_active else (0.15, 0.17, 0.20, 1.0),
                color=(1, 1, 1, 1),
                **font_kw
            )
            b.bind(on_release=lambda inst, name=t_name: self.handle_bottom_tab(name))
            self.bottom_buttons[t_name] = b
            nav_bar.add_widget(b)
            
        root.add_widget(nav_bar)
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
            b.background_color = (1.0, 0.45, 0.0, 1.0) if s == name else (0.20, 0.22, 0.25, 1.0)

    def handle_bottom_tab(self, tab_name):
        for name, btn in self.bottom_buttons.items():
            btn.background_color = (1.0, 0.45, 0.0, 1.0) if name == tab_name else (0.15, 0.17, 0.20, 1.0)
        
        if tab_name == 'ایکس‌ری (X-Ray)':
            self.current_source = 'X-Ray'
            self.lbl1.text = fa('ولتاژ تیوب (kV):')
            self.in1.text = '200'
            self.lbl2.text = fa('جریان تیوب (mA):')
            self.in2.text = '4.0'
        elif tab_name == 'مرزبندی و حفاظ':
            self.current_source = 'Ir-192'
            self.lbl1.text = fa('اکتیویته چشمه (Ci):')
            self.in1.text = '50'
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
                output_rate = math.pow(kv / 100.0, 2.4) * 0.14 * ma * 60.0 * 10000.0
                safe_d = math.sqrt(max(0.1, output_rate) / 7.5)
                hvl_fe = 4.0 + (kv / 50.0)
                thick_factor = math.pow(2.0, max(0.0, thick) / hvl_fe)
                sec = (45.0 * thick_factor * dist_factor) / (ma * (kv / 150.0))
                info_text = f"ایکس‌ری: {int(kv)}kV | جریان: {ma}mA"
            else:
                curie = max(0.01, v1)
                shield = max(0.0, v2)
                iso = ISOTOPES[self.current_source]
                trans = math.pow(2.0, -(shield / iso['hvl_pb'])) if iso['hvl_pb'] > 0 else 1.0
                dose_rate_1m = iso['gamma'] * curie * 10000.0 * trans
                safe_d = math.sqrt(max(0.1, dose_rate_1m) / 7.5)
                thick_factor = math.pow(2.0, max(0.0, thick) / iso['hvl_fe'])
                sec = (iso['factor'] * thick_factor * dist_factor * 120.0) / (curie / 10.0)
                info_text = f"ایزوتوپ: {self.current_source} | تضعیف حفاظت: {trans:.2f}"

            safe_d = round(safe_d, 2)
            op_d = round(safe_d * 1.25, 2)
            sec = round(max(1.0, sec), 1)

            m = int(sec // 60)
            s = int(sec % 60)
            t_txt = f"{sec} ثانیه" if m == 0 else f"{m} دقیقه و {s} ثانیه"

            self.res_dist.text = fa(f'شعاع فاصله طناب‌کشی ایمن: {safe_d} متر')
            self.res_info.text = fa(info_text + f" | زمان: {t_txt}")
            self.res_op.text = fa(f'استقرار مجاز اپراتور: حداقل {op_d} متری چشمه')

        except Exception:
            self.res_dist.text = fa('خطا در ارقام ورودی!')
            self.res_info.text = fa('لطفاً اعداد را به انگلیسی وارد کنید')
            self.res_op.text = fa('')

if __name__ == '__main__':
    NDTMainApp().run()
