# -*- coding: utf-8 -*-
import os
import math
import arabic_reshaper
from bidi.algorithm import get_display

from kivy.app import App
from kivy.core.text import LabelBase
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.graphics import Color, RoundedRectangle
from kivy.core.window import Window
from kivy.resources import resource_add_path

# مسیر فعلی برنامه
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
resource_add_path(BASE_DIR)

# تنظیم و ثبت فونت فارسی
FONT_FILE = os.path.join(BASE_DIR, 'font.ttf')
if os.path.exists(FONT_FILE):
    try:
        LabelBase.register(name='VazirFont', fn_regular=FONT_FILE)
        APP_FONT = 'VazirFont'
    except Exception:
        APP_FONT = 'Roboto'
else:
    APP_FONT = 'Roboto'

def f(text):
    """تبدیل متن فارسی به فرمت RTL صحیح"""
    if not text:
        return ""
    try:
        reshaped = arabic_reshaper.reshape(str(text))
        return get_display(reshaped)
    except Exception:
        return str(text)

ISOTOPES = {
    'Ir-192': {'gamma': 0.48, 'name': 'ایریدیم ۱۹۲'},
    'Se-75':  {'gamma': 0.20, 'name': 'سلنیوم ۷۵'},
    'Co-60':  {'gamma': 1.30, 'name': 'کبالت ۶۰'},
    'Cs-137': {'gamma': 0.32, 'name': 'سزیم ۱۳۷'}
}

class NDTGammaApp(App):
    def build(self):
        Window.clearcolor = (0.07, 0.08, 0.09, 1)  # #121416
        self.selected_iso = 'Ir-192'
        self.iso_buttons = {}

        root = BoxLayout(orientation='vertical', padding=12, spacing=10)

        # 1. هدر بالا با لوگوی شرکت
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=65, spacing=10)
        
        logo_path = os.path.join(BASE_DIR, 'logo.png')
        if os.path.exists(logo_path):
            logo_img = Image(source=logo_path, size_hint=(None, 1), width=65)
            header.add_widget(logo_img)
        
        title_box = BoxLayout(orientation='vertical')
        t1 = Label(text=f("محاسبه فاصله ایمن رادیوگرافی"), font_name=APP_FONT, font_size='17sp', bold=True, color=(1, 0.48, 0, 1))
        t2 = Label(text="NDT Gamma Radiation Calculator", font_size='11sp', color=(0.7, 0.7, 0.7, 1))
        title_box.add_widget(t1)
        title_box.add_widget(t2)
        header.add_widget(title_box)
        root.add_widget(header)

        # دکمه تماس با ما بالای صفحه
        contact_bar = BoxLayout(size_hint_y=None, height=36)
        btn_contact = Button(
            text=f("اطلاعات شرکت و تماس با ما  ☎"),
            font_name=APP_FONT,
            font_size='13sp',
            background_color=(0.2, 0.5, 0.9, 1)
        )
        btn_contact.bind(on_release=self.show_contact_popup)
        contact_bar.add_widget(btn_contact)
        root.add_widget(contact_bar)

        # 2. اسکرول برای بخش ورودی‌ها
        scroll = ScrollView(size_hint=(1, 1))
        body = BoxLayout(orientation='vertical', spacing=10, size_hint_y=None)
        body.bind(minimum_height=body.setter('height'))

        # انتخاب چشمه
        body.add_widget(Label(text=f("انتخاب ایزوتوپ پرتوزا:"), font_name=APP_FONT, font_size='14sp', size_hint_y=None, height=28, color=(1, 1, 1, 1)))
        
        iso_grid = GridLayout(cols=4, spacing=6, size_hint_y=None, height=45)
        for iso_key in ISOTOPES.keys():
            b = Button(text=iso_key, bold=True, font_size='13sp')
            b.bind(on_release=lambda instance, k=iso_key: self.select_isotope(k))
            self.iso_buttons[iso_key] = b
            iso_grid.add_widget(b)
        body.add_widget(iso_grid)
        self.update_iso_buttons_ui()

        # اکتیویته
        body.add_widget(Label(text=f("اکتیویته چشمه (کوری - Curie):"), font_name=APP_FONT, font_size='13sp', size_hint_y=None, height=26, color=(0.85, 0.85, 0.85, 1)))
        self.txt_act = TextInput(text="50", multiline=False, input_filter='float', size_hint_y=None, height=44, font_size='15sp')
        body.add_widget(self.txt_act)

        # حد دوز
        body.add_widget(Label(text=f("حد دوز مجاز (میکروسِوِرت بر ساعت - μSv/h):"), font_name=APP_FONT, font_size='13sp', size_hint_y=None, height=26, color=(0.85, 0.85, 0.85, 1)))
        self.txt_limit = TextInput(text="7.5", multiline=False, input_filter='float', size_hint_y=None, height=44, font_size='15sp')
        body.add_widget(self.txt_limit)

        # دکمه محاسبه
        btn_calc = Button(
            text=f("محاسبه فاصله ایمن (متر)"),
            font_name=APP_FONT,
            font_size='16sp',
            bold=True,
            size_hint_y=None,
            height=48,
            background_color=(1, 0.48, 0, 1)
        )
        btn_calc.bind(on_release=self.calculate_distance)
        body.add_widget(btn_calc)

        # کادر نمایش نتیجه
        self.lbl_result = Label(
            text=f("برای محاسبه دکمه بالا را بزنید"),
            font_name=APP_FONT,
            font_size='15sp',
            bold=True,
            size_hint_y=None,
            height=65,
            color=(0.2, 0.9, 0.3, 1)
        )
        body.add_widget(self.lbl_result)

        scroll.add_widget(body)
        root.add_widget(scroll)

        return root

    def select_isotope(self, iso_key):
        self.selected_iso = iso_key
        self.update_iso_buttons_ui()

    def update_iso_buttons_ui(self):
        for k, b in self.iso_buttons.items():
            if k == self.selected_iso:
                b.background_color = (1, 0.48, 0, 1)
            else:
                b.background_color = (0.25, 0.28, 0.32, 1)

    def calculate_distance(self, *args):
        try:
            curie = float(self.txt_act.text.strip())
            limit = float(self.txt_limit.text.strip())
            if limit <= 0 or curie <= 0:
                self.lbl_result.text = f("خطا: مقادیر باید بزرگتر از صفر باشند")
                self.lbl_result.color = (1, 0.2, 0.2, 1)
                return

            gamma = ISOTOPES[self.selected_iso]['gamma']
            # فرمول: r = sqrt((A * Gamma * 1000) / Dose_Limit)
            dist = math.sqrt((curie * gamma * 1000.0) / limit)
            
            res_text = f"فاصله ایمن مرزبندی: {dist:.2f} متر\nایزوتوپ: {self.selected_iso} | اکتیویته: {curie} Ci"
            self.lbl_result.text = f(res_text)
            self.lbl_result.color = (0.2, 1, 0.4, 1)
        except Exception:
            self.lbl_result.text = f("خطا در ورودی! لطفاً اعداد را درست وارد کنید")
            self.lbl_result.color = (1, 0.2, 0.2, 1)

    def show_contact_popup(self, *args):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=8)
        
        banner_path = os.path.join(BASE_DIR, 'company_banner.png')
        if os.path.exists(banner_path):
            img = Image(source=banner_path, size_hint=(1, 0.45))
            layout.add_widget(img)
            
        t_company = Label(
            text=f("شرکت رادیوگرافی صنعتی ایران"),
            font_name=APP_FONT,
            font_size='16sp',
            bold=True,
            color=(1, 0.5, 0, 1),
            size_hint_y=None,
            height=30
        )
        layout.add_widget(t_company)

        t_phones = Label(
            text="09122012248\n09121042253\n09121326011",
            font_size='14sp',
            bold=True,
            color=(1, 1, 1, 1),
            size_hint_y=None,
            height=60
        )
        layout.add_widget(t_phones)

        btn_close = Button(
            text=f("بستن"),
            font_name=APP_FONT,
            size_hint=(1, None),
            height=40,
            background_color=(0.8, 0.2, 0.2, 1)
        )
        layout.add_widget(btn_close)

        popup = Popup(
            title=f("اطلاعات تماس"),
            title_font=APP_FONT,
            content=layout,
            size_hint=(0.9, 0.75),
            auto_dismiss=True
        )
        btn_close.bind(on_release=popup.dismiss)
        popup.open()

if __name__ == '__main__':
    NDTGammaApp().run()
