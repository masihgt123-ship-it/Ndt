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
from kivy.graphics import Color, RoundedRectangle, Line, Rectangle

import ndt_calculator as calc

# Window background base color
Window.clearcolor = (0.06, 0.07, 0.08, 1.0)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_asset_path(filename):
    """Finds image or font assets with multiple fallbacks"""
    candidates = [
        os.path.join(BASE_DIR, filename),
        os.path.join(BASE_DIR, 'assets', filename),
        filename
    ]
    for p in candidates:
        if os.path.isfile(p):
            return p
    return filename

FONT_NAME = get_asset_path('font.ttf')

def fa(text):
    """Prepares Persian string for RTL rendering in Kivy"""
    try:
        if not text:
            return ""
        reshaped = arabic_reshaper.reshape(str(text))
        return get_display(reshaped)
    except Exception:
        return str(text)

class ModernCard(BoxLayout):
    """Industrial dark glassmorphism card"""
    def __init__(self, bg_color=(0.11, 0.13, 0.15, 0.92), border_color=(0.22, 0.25, 0.28, 1.0), radius=12, **kwargs):
        super(ModernCard, self).__init__(**kwargs)
        self.bg_color = bg_color
        self.border_color = border_color
        self.radius = radius
        with self.canvas.before:
            self.col_bg = Color(*self.bg_color)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[self.radius])
            self.col_border = Color(*self.border_color)
            self.border = Line(rounded_rectangle=[self.x, self.y, self.width, self.height, self.radius], width=1.1)
        self.bind(pos=self._update_shape, size=self._update_shape)

    def _update_shape(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
        self.border.rounded_rectangle = [self.x, self.y, self.width, self.height, self.radius]

class StyledInput(TextInput):
    """Dark-themed numeric input"""
    def __init__(self, **kwargs):
        super(StyledInput, self).__init__(**kwargs)
        self.background_normal = ''
        self.background_active = ''
        self.background_color = (0.08, 0.09, 0.10, 1.0)
        self.foreground_color = (1.0, 0.85, 0.30, 1.0)
        self.cursor_color = (1.0, 0.48, 0.0, 1.0)
        self.font_size = sp(15)
        self.multiline = False
        self.halign = 'center'
        self.padding = [dp(6), dp(8), dp(6), dp(8)]
        with self.canvas.after:
            Color(0.25, 0.28, 0.32, 1.0)
            self.border_line = Line(rounded_rectangle=[self.x, self.y, self.width, self.height, 6], width=1.0)
        self.bind(pos=self._update_input_border, size=self._update_input_border)

    def _update_input_border(self, *args):
        self.border_line.rounded_rectangle = [self.x, self.y, self.width, self.height, 6]

class NDTMainApp(App):
    def build(self):
        self.title = 'رادیوگرافی صنعتی'
        self.current_source = 'Ir-192'
        self.source_buttons = {}

        root = FloatLayout()

        # Background wallpaper with dark overlay
        bg_file = get_asset_path('bg.png')
        if os.path.isfile(bg_file):
            with root.canvas.before:
                self.bg_img = Rectangle(source=bg_file, pos=root.pos, size=root.size)
                Color(0.04, 0.05, 0.06, 0.88)
                self.overlay = Rectangle(pos=root.pos, size=root.size)
            root.bind(pos=self._update_bg, size=self._update_bg)

        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        content = BoxLayout(orientation='vertical', size_hint_y=None, padding=dp(12), spacing=dp(10))
        content.bind(minimum_height=content.setter('height'))

        # Header Banner
        banner_card = ModernCard(size_hint_y=None, height=dp(70), padding=dp(8), spacing=dp(10))
        logo_path = get_asset_path('logo.png')
        if os.path.isfile(logo_path):
            logo_img = Image(source=logo_path, size_hint=(None, 1), width=dp(55))
            banner_card.add_widget(logo_img)

        title_box = BoxLayout(orientation='vertical')
        app_title = Label(
            text=fa('شرکت رادیوگرافی صنعتی ایران'),
            font_name=FONT_NAME,
            font_size=sp(15),
            bold=True,
            color=(1.0, 0.55, 0.0, 1.0)
        )
        sub_title = Label(
            text=fa('محاسبات تخصصی دوز، فاصله ایمن و اکسپوژر'),
            font_name=FONT_NAME,
            font_size=sp(11),
            color=(0.75, 0.78, 0.82, 1.0)
        )
        title_box.add_widget(app_title)
        title_box.add_widget(sub_title)
        banner_card.add_widget(title_box)
        content.add_widget(banner_card)

        # Source Selection Tabs (Gamma + X-Ray)
        tab_card = ModernCard(orientation='vertical', size_hint_y=None, height=dp(85), padding=dp(8), spacing=dp(6))
        tab_label = Label(text=fa('انتخاب منبع پرتو:'), font_name=FONT_NAME, font_size=sp(12), color=(0.8, 0.8, 0.8, 1.0), size_hint_y=None, height=dp(20))
        tab_card.add_widget(tab_label)

        btn_grid = GridLayout(cols=5, spacing=dp(6), size_hint_y=None, height=dp(44))
        sources = ['Ir-192', 'Se-75', 'Co-60', 'Cs-137', 'X-Ray']
        
        for s in sources:
            btn = Button(
                text=s,
                font_name=FONT_NAME,
                font_size=sp(12),
                bold=True,
                background_normal='',
                background_color=(1.0, 0.48, 0.0, 1.0) if s == self.current_source else (0.16, 0.18, 0.20, 1.0),
                color=(1.0, 1.0, 1.0, 1.0)
            )
            btn.bind(on_release=lambda instance, src=s: self.select_source(src))
            self.source_buttons[s] = btn
            btn_grid.add_widget(btn)

        tab_card.add_widget(btn_grid)
        content.add_widget(tab_card)

        # Dynamic Inputs Card
        self.input_card = ModernCard(orientation='vertical', size_hint_y=None, height=dp(240), padding=dp(10), spacing=dp(8))
        self.inputs_grid = GridLayout(cols=2, spacing=dp(10), size_hint_y=1)

        # Row 1: Primary Strength (Curie or kV)
        self.lbl_param1 = Label(text=fa('اکتیویته چشمه (Ci):'), font_name=FONT_NAME, font_size=sp(12), color=(0.9, 0.9, 0.9, 1.0))
        self.in_param1 = StyledInput(text='50')
        self.inputs_grid.add_widget(self.in_param1)
        self.inputs_grid.add_widget(self.lbl_param1)

        # Row 2: Secondary Strength (X-Ray mA or Collimator Shield)
        self.lbl_param2 = Label(text=fa('ضخامت شیلد سرب (mm):'), font_name=FONT_NAME, font_size=sp(12), color=(0.9, 0.9, 0.9, 1.0))
        self.in_param2 = StyledInput(text='0')
        self.inputs_grid.add_widget(self.in_param2)
        self.inputs_grid.add_widget(self.lbl_param2)

        # Row 3: Pipe / Steel thickness (mm)
        self.lbl_thick = Label(text=fa('ضخامت فولاد (mm):'), font_name=FONT_NAME, font_size=sp(12), color=(0.9, 0.9, 0.9, 1.0))
        self.in_thick = StyledInput(text='12')
        self.inputs_grid.add_widget(self.in_thick)
        self.inputs_grid.add_widget(self.lbl_thick)

        # Row 4: SFD (cm)
        self.lbl_sfd = Label(text=fa('فاصله SFD (cm):'), font_name=FONT_NAME, font_size=sp(12), color=(0.9, 0.9, 0.9, 1.0))
        self.in_sfd = StyledInput(text='60')
        self.inputs_grid.add_widget(self.in_sfd)
        self.inputs_grid.add_widget(self.lbl_sfd)

        self.input_card.add_widget(self.inputs_grid)
        content.add_widget(self.input_card)

        # Action Button: Calculate
        self.calc_btn = Button(
            text=fa('محاسبه فاصله ایمن و زمان اکسپوژر'),
            font_name=FONT_NAME,
            font_size=sp(15),
            bold=True,
            size_hint_y=None,
            height=dp(48),
            background_normal='',
            background_color=(1.0, 0.45, 0.0, 1.0),
            color=(1, 1, 1, 1)
        )
        self.calc_btn.bind(on_release=self.perform_calculation)
        content.add_widget(self.calc_btn)

        # Results Dashboard Card
        self.res_card = ModernCard(
            orientation='vertical',
            bg_color=(0.10, 0.12, 0.13, 0.95),
            border_color=(1.0, 0.50, 0.0, 0.7),
            size_hint_y=None,
            height=dp(170),
            padding=dp(12),
            spacing=dp(6)
        )
        
        self.res_title = Label(text=fa('نتایج محاسبات ایمنی و پرتوگیری:'), font_name=FONT_NAME, font_size=sp(13), bold=True, color=(1.0, 0.75, 0.2, 1.0), size_hint_y=None, height=dp(24))
        self.res_distance = Label(text=fa('فاصله طناب‌کشی ایمن: -- متر'), font_name=FONT_NAME, font_size=sp(15), bold=True, color=(0.2, 1.0, 0.5, 1.0))
        self.res_operator = Label(text=fa('موقعیت مجاز اپراتور: -- متر'), font_name=FONT_NAME, font_size=sp(12), color=(0.85, 0.88, 0.9, 1.0))
        self.res_time = Label(text=fa('زمان تخمینی اکسپوژر: -- ثانیه'), font_name=FONT_NAME, font_size=sp(14), bold=True, color=(1.0, 0.85, 0.2, 1.0))

        self.res_card.add_widget(self.res_title)
        self.res_card.add_widget(self.res_distance)
        self.res_card.add_widget(self.res_operator)
        self.res_card.add_widget(self.res_time)
        content.add_widget(self.res_card)

        # Emergency & Support Footer
        footer = Label(
            text=fa('تماس پشتیبانی: 09122012248 - 09121042253'),
            font_name=FONT_NAME,
            font_size=sp(11),
            color=(0.55, 0.60, 0.65, 1.0),
            size_hint_y=None,
            height=dp(25)
        )
        content.add_widget(footer)

        scroll.add_widget(content)
        root.add_widget(scroll)
        
        self.select_source('Ir-192')
        return root

    def _update_bg(self, *args):
        if hasattr(self, 'bg_img'):
            self.bg_img.pos = Window.pos
            self.bg_img.size = Window.size
            self.overlay.pos = Window.pos
            self.overlay.size = Window.size

    def select_source(self, source_name):
        self.current_source = source_name
        for s, btn in self.source_buttons.items():
            if s == source_name:
                btn.background_color = (1.0, 0.48, 0.0, 1.0)
            else:
                btn.background_color = (0.16, 0.18, 0.20, 1.0)

        # Adjust UI labels and defaults when switching between Gamma and X-Ray
        if source_name == 'X-Ray':
            self.lbl_param1.text = fa('ولتاژ تیوب (kV):')
            self.in_param1.text = '200'
            self.lbl_param2.text = fa('جریان تیوب (mA):')
            self.in_param2.text = '4.0'
        else:
            self.lbl_param1.text = fa('اکتیویته چشمه (Ci):')
            self.in_param1.text = '45'
            self.lbl_param2.text = fa('شیلد سرب کولیماتور (mm):')
            self.in_param2.text = '0'

    def perform_calculation(self, *args):
        try:
            val1 = float(self.in_param1.text.strip() or '0')
            val2 = float(self.in_param2.text.strip() or '0')
            thick = float(self.in_thick.text.strip() or '10')
            sfd = float(self.in_sfd.text.strip() or '60')

            if self.current_source == 'X-Ray':
                kv = val1
                ma = val2
                safe_dist = calc.calculate_xray_safe_distance(kv=kv, ma=ma, lead_shield_mm=0.0, limit_dose=7.5)
                exp_seconds = calc.calculate_exposure_time('X-Ray', activity_or_ma=ma, kv=kv, thickness_mm=thick, sfd_cm=sfd)
            else:
                curie = val1
                shield = val2
                safe_dist = calc.calculate_gamma_safe_distance(self.current_source, curie=curie, lead_shield_mm=shield, limit_dose=7.5)
                exp_seconds = calc.calculate_exposure_time(self.current_source, activity_or_ma=curie, thickness_mm=thick, sfd_cm=sfd)

            operator_dist = round(safe_dist * 1.25, 2)
            
            # Format time display (minutes and seconds)
            mins = int(exp_seconds // 60)
            secs = int(exp_seconds % 60)
            time_str = f"{exp_seconds} ثانیه" if mins == 0 else f"{mins} دقیقه و {secs} ثانیه"

            self.res_distance.text = fa(f'شعاع طناب‌کشی ایمن: {safe_dist} متر')
            self.res_operator.text = fa(f'فاصله مجاز استقرار اپراتور: {operator_dist} متر')
            self.res_time.text = fa(f'زمان تخمینی اکسپوژر: {time_str}')

        except Exception as err:
            self.res_distance.text = fa('خطا در ارقام ورودی!')
            self.res_operator.text = fa('لطفاً اعداد را به انگلیسی و صحیح وارد کنید.')
            self.res_time.text = fa('')

if __name__ == '__main__':
    NDTMainApp().run()
