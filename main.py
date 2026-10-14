# -*- coding: utf-8 -*-
import math
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
fromKivy.uix.button import Button # type: ignore
from kivy.uix.image import Image
from kivy.uix.modalview import ModalView
from kivy.graphics import Color, RoundedRectangle, Line

# بررسی و بارگذاری کتابخانه RTL
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    def fa(text):
        if not text:
            return ""
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
except ImportError:
    def fa(text):
        return text

FONT_PATH = "font.ttf"

# ثابت‌های گاما برای ایزوتوپ‌های صنعتی (R * m^2 / (hr * Ci))
ISOTOPES = {
    "Ir-192": {"name": "Ir-192", "gamma": 0.48, "fa_name": "ایریدیوم ۱۹۲"},
    "Se-75":  {"name": "Se-75",  "gamma": 0.20, "fa_name": "سلنیوم ۷۵"},
    "Co-60":  {"name": "Co-60",  "gamma": 1.32, "fa_name": "کبالت ۶۰"},
    "Cs-137": {"name": "Cs-137", "gamma": 0.33, "fa_name": "سزیوم ۱۳۷"}
}

COMPANY_PHONES = ["09122012248", "09121042253", "09121326011"]

class RoundedCard(BoxLayout):
    def __init__(self, bg_color=(0.11, 0.13, 0.16, 1), border_color=(0.2, 0.25, 0.3, 1), radius=16, **kwargs):
        super(RoundedCard, self).__init__(**kwargs)
        self.bg_color = bg_color
        self.border_color = border_color
        self.radius = radius
        with self.canvas.before:
            self.color_bg = Color(*self.bg_color)
            self.rect_bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[self.radius])
            self.color_line = Color(*self.border_color)
            self.line_border = Line(rounded_rectangle=[self.x, self.y, self.width, self.height, self.radius], width=1.5)
        self.bind(pos=self._update_shape, size=self._update_shape)

    def _update_shape(self, *args):
        self.rect_bg.pos = self.pos
        self.rect_bg.size = self.size
        self.line_border.rounded_rectangle = [self.x, self.y, self.width, self.height, self.radius]


class NDTCalculatorApp(App):
    def build(self):
        Window.clearcolor = (0.07, 0.08, 0.09, 1)  # رنگ پس‌زمینه تیره صنعتی
        self.selected_isotope = "Ir-192"
        self.iso_buttons = {}

        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True)
        root = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            padding=[20, 18, 20, 24],
            spacing=16
        )
        root.bind(minimum_height=root.setter('height'))

        # ----------------- هدر و لوگوی اصلی -----------------
        header_box = BoxLayout(orientation='vertical', size_hint_y=None, height=160, spacing=6)
        
        try:
            logo_img = Image(source='logo.png', size_hint=(None, None), size=(84, 84), pos_hint={'center_x': 0.5})
            header_box.add_widget(logo_img)
        except Exception:
            pass

        title_lbl = Label(
            text=fa("محاسبه‌گر فاصله ایمن رادیوگرافی"),
            font_name=FONT_PATH,
            font_size='20sp',
            bold=True,
            color=(0.95, 0.95, 0.97, 1),
            size_hint_y=None,
            height=36
        )
        company_btn = Button(
            text=fa("شرکت رادیوگرافی صنعتی ایران [ تماس با ما ]"),
            font_name=FONT_PATH,
            font_size='14sp',
            color=(1.0, 0.55, 0.1, 1),
            background_normal='',
            background_color=(0, 0, 0, 0),
            size_hint_y=None,
            height=30
        )
        company_btn.bind(on_release=self.show_contact_modal)
        
        header_box.add_widget(title_lbl)
        header_box.add_widget(company_btn)
        root.add_widget(header_box)

        # ----------------- هشدار ایمنی -----------------
        warning_banner = RoundedCard(
            bg_color=(1.0, 0.45, 0.0, 0.95),
            border_color=(1.0, 0.6, 0.2, 1),
            radius=12,
            size_hint_y=None,
            height=50,
            padding=[12, 8]
        )
        warn_lbl = Label(
            text=fa("⚠  منطقه کنترل‌شده پرتو - رعایت اصول ایمنی الزامی است  ⚠"),
            font_name=FONT_PATH,
            font_size='13sp',
            bold=True,
            color=(0.07, 0.07, 0.07, 1)
        )
        warning_banner.add_widget(warn_lbl)
        root.add_widget(warning_banner)

        # ----------------- انتخاب ایزوتوپ -----------------
        iso_card = RoundedCard(
            orientation='vertical',
            size_hint_y=None,
            height=110,
            padding=[14, 12],
            spacing=10
        )
        iso_title = Label(
            text=fa("انتخاب ایزوتوپ رادیواکتیو"),
            font_name=FONT_PATH,
            font_size='15sp',
            bold=True,
            color=(0.85, 0.88, 0.92, 1),
            size_hint_y=None,
            height=24
        )
        iso_card.add_widget(iso_title)

        grid_iso = GridLayout(cols=4, spacing=10, size_hint_y=None, height=48)
        for key in ["Ir-192", "Se-75", "Co-60", "Cs-137"]:
            btn = Button(
                text=key,
                font_size='15sp',
                bold=True,
                background_normal='',
                background_color=(1.0, 0.48, 0.0, 1) if key == "Ir-192" else (0.16, 0.19, 0.23, 1),
                color=(1, 1, 1, 1)
            )
            btn.bind(on_release=lambda instance, k=key: self.select_isotope(k))
            self.iso_buttons[key] = btn
            grid_iso.add_widget(btn)

        iso_card.add_widget(grid_iso)
        root.add_widget(iso_card)

        # ----------------- ورودی‌ها (اکتیویته و دوز) -----------------
        inputs_row = BoxLayout(spacing=12, size_hint_y=None, height=115)

        # اکتیویته
        card_act = RoundedCard(orientation='vertical', padding=[12, 10], spacing=8)
        card_act.add_widget(Label(
            text=fa("اکتیویته چشمه (Ci)"),
            font_name=FONT_PATH,
            font_size='14sp',
            bold=True,
            color=(0.85, 0.88, 0.92, 1),
            size_hint_y=None,
            height=22
        ))
        self.input_activity = TextInput(
            text="40",
            multiline=False,
            input_filter='float',
            font_size='20sp',
            halign='center',
            background_normal='',
            background_color=(0.08, 0.
