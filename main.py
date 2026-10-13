# -*- coding: utf-8 -*-
import os
import math
from kivy.app import App
from kivy.core.text import LabelBase
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.graphics import Color, RoundedRectangle
from kivy.core.window import Window

# ----------------- بارگذاری فونت فارسی -----------------
FONT_NAME = 'Roboto'
if os.path.exists('font.ttf'):
    LabelBase.register(name='VazirFont', fn_regular='font.ttf')
    FONT_NAME = 'VazirFont'

# ----------------- اصلاح متون فارسی (RTL) -----------------
def fa(text):
    if not text:
        return ""
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except Exception:
        return text

# ----------------- رنگ‌های تم صنعتی (Design 5) -----------------
COLOR_BG = (0.07, 0.08, 0.09, 1)          # مشکی زغالی
COLOR_CARD = (0.12, 0.14, 0.16, 1)        # خاکستری تیره پنل‌ها
COLOR_ORANGE = (1.0, 0.48, 0.0, 1)        # نارنجی ایمنی پرتونگاری (#FF7A00)
COLOR_TEXT_MAIN = (0.95, 0.95, 0.95, 1)   # سفید روشن
COLOR_MUTED = (0.60, 0.65, 0.70, 1)       # خاکستری مات
COLOR_INPUT_BG = (0.16, 0.18, 0.22, 1)    # فیلد ورودی

ISOTOPES = {
    'Ir-192': {'gamma': 0.13, 'half_life': 73.83},
    'Se-75':  {'gamma': 0.054, 'half_life': 119.8},
    'Co-60':  {'gamma': 0.35, 'half_life': 1925.0},
    'Cs-137': {'gamma': 0.081, 'half_life': 11000.0}
}

class NDTCalculatorApp(App):
    def build(self):
        Window.clearcolor = COLOR_BG
        self.selected_iso = 'Ir-192'

        root_scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        main_layout = BoxLayout(orientation='vertical', padding=16, spacing=12, size_hint_y=None)
        main_layout.bind(minimum_height=main_layout.setter('height'))

        # 1. بنر عنوان
        title_box = BoxLayout(orientation='vertical', size_hint_y=None, height=60)
        with title_box.canvas.before:
            Color(*COLOR_CARD)
            self.rect_title = RoundedRectangle(size=title_box.size, pos=title_box.pos, radius=[10])
        title_box.bind(pos=lambda obj, val: setattr(self.rect_title, 'pos', val),
                       size=lambda obj, val: setattr(self.rect_title, 'size', val))

        title_lbl = Label(
            text=fa("محاسبه‌گر ایمنی پرتونگاری صنعتی (NDT)"),
            font_name=FONT_NAME,
            font_size='17sp',
            bold=True,
            color=COLOR_ORANGE,
            halign='center'
        )
        title_box.add_widget(title_lbl)
        main_layout.add_widget(title_box)

        # 2. نوار هشدار
        warn_box = BoxLayout(size_hint_y=None, height=42, padding=6)
        with warn_box.canvas.before:
            Color(0.25, 0.10, 0.0, 0.8)
            self.rect_warn = RoundedRectangle(size=warn_box.size, pos=warn_box.pos, radius=[8])
        warn_box.bind(pos=lambda obj, val: setattr(self.rect_warn, 'pos', val),
                      size=lambda obj, val: setattr(self.rect_warn, 'size', val))

        warn_lbl = Label(
            text=fa("استاندارد ایمنی: حد دوز مجاز طناب‌کشی ۲.۵ میکروسیورت بر ساعت"),
            font_name=FONT_NAME,
            font_size='11sp',
            color=COLOR_ORANGE,
            halign='center'
        )
        warn_box.add_widget(warn_lbl)
        main_layout.add_widget(warn_box)

        # 3. انتخاب ایزوتوپ
        iso_lbl = Label(
            text=fa("انتخاب ایزوتوپ صنعتی:"),
            font_name=FONT_NAME,
            font_size='13sp',
            size_hint_y=None,
            height=26,
            color=COLOR_MUTED,
            halign='right'
        )
        iso_lbl.bind(size=iso_lbl.setter('text_size'))
        main_layout.add_widget(iso_lbl)

        btn_grid = GridLayout(cols=4, spacing=8, size_hint_y=None, height=45)
        self.iso_buttons = {}
        for iso_key in ISOTOPES.keys():
            btn = Button(
                text=iso_key,
                font_name=FONT_NAME,
                bold=True,
                background_normal='',
                background_color=COLOR_ORANGE if iso_key == self.selected_iso else COLOR_CARD,
                color=COLOR_BG if iso_key == self.selected_iso else COLOR_TEXT_MAIN
            )
            btn.bind(on_release=lambda instance, k=iso_key: self.select_isotope(k))
            self.iso_buttons[iso_key] = btn
            btn_grid.add_widget(btn)
        main_layout.add_widget(btn_grid)

        # 4. ورودی‌ها
        inputs_box = BoxLayout(orientation='vertical', spacing=8, size_hint_y=None, height=175, padding=12)
        with inputs_box.canvas.before:
            Color(*COLOR_CARD)
            self.rect_inp = RoundedRectangle(size=inputs_box.size, pos=inputs_box.pos, radius=[10])
        inputs_box.bind(pos=lambda obj, val: setattr(self.rect_inp, 'pos', val),
                        size=lambda obj, val: setattr(self.rect_inp, 'size', val))

        lbl_act = Label(text=fa("اکتیویته چشمه (گیگابکرل - GBq):"), font_name=FONT_NAME, font_size='12sp', color=COLOR_TEXT_MAIN, size_hint_y=None, height=20, halign='right')
        lbl_act.bind(size=lbl_act.setter('text_size'))
        inputs_box.add_widget(lbl_act)
        self.txt_act = TextInput(text="1850", multiline=False, font_size='15sp', background_color=COLOR_INPUT_BG, foreground_color=COLOR_TEXT_MAIN, cursor_color=COLOR_ORANGE, size_hint_y=None, height=38)
        inputs_box.add_widget(self.txt_act)

        lbl_dose = Label(text=fa("حد دوز مجاز (میکروسیورت بر ساعت - μSv/h):"), font_name=FONT_NAME, font_size='12sp', color=COLOR_TEXT_MAIN, size_hint_y=None, height=20, halign='right')
        lbl_dose.bind(size=lbl_dose.setter('text_size'))
        inputs_box.add_widget(lbl_dose)
        self.txt_dose = TextInput(text="2.5", multiline=False, font_size='15sp', background_color=COLOR_INPUT_BG, foreground_color=COLOR_TEXT_MAIN, cursor_color=COLOR_ORANGE, size_hint_y=None, height=38)
        inputs_box.add_widget(self.txt_dose)

        main_layout.add_widget(inputs_box)

        # 5. دکمه محاسبه
        calc_btn = Button(
            text=fa("محاسبه حریم کنترل‌شده"),
            font_name=FONT_NAME,
            font_size='15sp',
            bold=True,
            background_normal='',
            background_color=COLOR_ORANGE,
            color=COLOR_BG,
            size_hint_y=None,
            height=48
        )
        calc_btn.bind(on_release=self.calculate)
        main_layout.add_widget(calc_btn)

        # 6. کارت نتایج
        result_box = BoxLayout(orientation='vertical', padding=12, spacing=4, size_hint_y=None, height=120)
        with result_box.canvas.before:
            Color(*COLOR_CARD)
            self.rect_res = RoundedRectangle(size=result_box.size, pos=result_box.pos, radius=[10])
        result_box.bind(pos=lambda obj, val: setattr(self.rect_res, 'pos', val),
                        size=lambda obj, val: setattr(self.rect_res, 'size', val))

        res_title = Label(text=fa("فاصله ایمن طناب‌کشی (شعاع):"), font_name=FONT_NAME, font_size='13sp', color=COLOR_MUTED)
        self.res_val = Label(text="-- متر", font_name=FONT_NAME, font_size='26sp', bold=True, color=COLOR_ORANGE)
        self.res_sub = Label(text=fa("بر اساس قانون عکس مجذور فاصله"), font_name=FONT_NAME, font_size='11sp', color=COLOR_MUTED)

        result_box.add_widget(res_title)
        result_box.add_widget(self.res_val)
        result_box.add_widget(self.res_sub)
        main_layout.add_widget(result_box)

        # 7. دکمه تماس با ما / درباره سازنده (Contact Us)
        contact_btn = Button(
            text=fa("ارتباط با سازنده (Contact Us)"),
            font_name=FONT_NAME,
            font_size='13sp',
            background_normal='',
            background_color=(0.14, 0.16, 0.19, 1),
            color=COLOR_ORANGE,
            size_hint_y=None,
            height=42
        )
        contact_btn.bind(on_release=self.show_contact_popup)
        main_layout.add_widget(contact_btn)

        root_scroll.add_widget(main_layout)
        return root_scroll

    def show_contact_popup(self, instance):
        content = BoxLayout(orientation='vertical', spacing=12, padding=16)

        header = Label(
            text=fa("شرکت رادیوگرافی صنعتی ایران"),
            font_name=FONT_NAME,
            font_size='16sp',
            bold=True,
            color=COLOR_ORANGE,
            size_hint_y=None,
            height=30
        )
        sub = Label(
            text=fa("مشاوره، بازرسی فنی و ایمنی پرتونگاری NDT"),
            font_name=FONT_NAME,
            font_size='11sp',
            color=COLOR_MUTED,
            size_hint_y=None,
            height=20
        )
        phones_box = BoxLayout(orientation='vertical', spacing=6, size_hint_y=None, height=95)
        
        p1 = Label(text="09122012248", font_size='15sp', bold=True, color=COLOR_TEXT_MAIN)
        p2 = Label(text="09121042253", font_size='15sp', bold=True, color=COLOR_TEXT_MAIN)
        p3 = Label(text="09121326011", font_size='15sp', bold=True, color=COLOR_TEXT_MAIN)
        
        phones_box.add_widget(p1)
        phones_box.add_widget(p2)
        phones_box.add_widget(p3)

        close_btn = Button(
            text=fa("بستن پنجره"),
            font_name=FONT_NAME,
            font_size='13sp',
            bold=True,
            background_normal='',
            background_color=COLOR_ORANGE,
            color=COLOR_BG,
            size_hint_y=None,
            height=40
        )

        content.add_widget(header)
        content.add_widget(sub)
        content.add_widget(phones_box)
        content.add_widget(close_btn)

        popup = Popup(
            title="",
            separator_height=0,
            content=content,
            size_hint=(0.88, 0.48),
            background_color=(0.10, 0.12, 0.14, 0.95),
            auto_dismiss=True
        )
        close_btn.bind(on_release=popup.dismiss)
        popup.open()

    def select_isotope(self, iso_key):
        self.selected_iso = iso_key
        for key, btn in self.iso_buttons.items():
            if key == iso_key:
                btn.background_color = COLOR_ORANGE
                btn.color = COLOR_BG
            else:
                btn.background_color = COLOR_CARD
                btn.color = COLOR_TEXT_MAIN

    def calculate(self, instance):
        try:
            A = float(self.txt_act.text.strip())
            limit = float(self.txt_dose.text.strip())
            gamma = ISOTOPES[self.selected_iso]['gamma']
            
            # r = sqrt((A * gamma * 1000) / limit)
            r = math.sqrt((A * gamma * 1000.0) / limit)
            
            self.res_val.text = f"{r:.2f} " + fa("متر")
            self.res_sub.text = fa(f"ایزوتوپ: {self.selected_iso} | ضریب گاما: {gamma}")
        except Exception:
            self.res_val.text = fa("خطا در ورودی")
            self.res_sub.text = fa("لطفاً مقادیر عددی انگلیسی وارد کنید")

if __name__ == '__main__':
    NDTCalculatorApp().run()
