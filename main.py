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
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.core.window import Window

# ----------------- بارگذاری فونت فارسی -----------------
FONT_NAME = 'Roboto'
if os.path.exists('font.ttf'):
    LabelBase.register(name='VazirFont', fn_regular='font.ttf')
    FONT_NAME = 'VazirFont'

# ----------------- تبدیل و اصلاح متن فارسی -----------------
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

# ----------------- تم مشکی و نارنجی صنعتی (Design 5) -----------------
COLOR_BG = (0.07, 0.08, 0.09, 1)          # مشکی زغالی
COLOR_CARD = (0.12, 0.14, 0.16, 1)        # خاکستری تیره پنل‌ها
COLOR_ORANGE = (1.0, 0.48, 0.0, 1)        # نارنجی ایمنی صنعتی (#FF7A00)
COLOR_TEXT_MAIN = (0.95, 0.95, 0.95, 1)   # سفید با کنتراست بالا
COLOR_MUTED = (0.60, 0.65, 0.70, 1)       # خاکستری روشن
COLOR_INPUT_BG = (0.16, 0.18, 0.22, 1)

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
        main_layout = BoxLayout(orientation='vertical', padding=18, spacing=14, size_hint_y=None)
        main_layout.bind(minimum_height=main_layout.setter('height'))

        # 1. بنر عنوان
        title_box = BoxLayout(orientation='vertical', size_hint_y=None, height=65)
        with title_box.canvas.before:
            Color(*COLOR_CARD)
            self.rect_title = RoundedRectangle(size=title_box.size, pos=title_box.pos, radius=[10])
        title_box.bind(pos=lambda obj, val: setattr(self.rect_title, 'pos', val),
                       size=lambda obj, val: setattr(self.rect_title, 'size', val))

        title_lbl = Label(
            text=fa("محاسبه‌گر ایمنی پرتونگاری گاما (NDT)"),
            font_name=FONT_NAME,
            font_size='18sp',
            bold=True,
            color=COLOR_ORANGE,
            halign='center'
        )
        title_box.add_widget(title_lbl)
        main_layout.add_widget(title_box)

        # 2. نوار هشدار تشعشع
        warn_box = BoxLayout(size_hint_y=None, height=45, padding=6)
        with warn_box.canvas.before:
            Color(0.25, 0.10, 0.0, 0.8)
            self.rect_warn = RoundedRectangle(size=warn_box.size, pos=warn_box.pos, radius=[8])
        warn_box.bind(pos=lambda obj, val: setattr(self.rect_warn, 'pos', val),
                      size=lambda obj, val: setattr(self.rect_warn, 'size', val))

        warn_lbl = Label(
            text=fa("استاندارد ایمنی: حد دوز مجاز عمومی ۲.۵ میکروسیورت بر ساعت"),
            font_name=FONT_NAME,
            font_size='12sp',
            color=COLOR_ORANGE,
            halign='center'
        )
        warn_box.add_widget(warn_lbl)
        main_layout.add_widget(warn_box)

        # 3. انتخاب رادیوایزوتوپ
        iso_lbl = Label(
            text=fa("انتخاب ایزوتوپ صنعتی:"),
            font_name=FONT_NAME,
            font_size='14sp',
            size_hint_y=None,
            height=28,
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

        # 4. کارت ورودی‌ها
        inputs_box = BoxLayout(orientation='vertical', spacing=10, size_hint_y=None, height=180, padding=12)
        with inputs_box.canvas.before:
            Color(*COLOR_CARD)
            self.rect_inp = RoundedRectangle(size=inputs_box.size, pos=inputs_box.pos, radius=[10])
        inputs_box.bind(pos=lambda obj, val: setattr(self.rect_inp, 'pos', val),
                        size=lambda obj, val: setattr(self.rect_inp, 'size', val))

        # اکتیویته
        lbl_act = Label(text=fa("اکتیویته چشمه (گیگابکرل - GBq):"), font_name=FONT_NAME, font_size='13sp', color=COLOR_TEXT_MAIN, size_hint_y=None, height=22, halign='right')
        lbl_act.bind(size=lbl_act.setter('text_size'))
        inputs_box.add_widget(lbl_act)
        self.txt_act = TextInput(text="1850", multiline=False, font_size='15sp', background_color=COLOR_INPUT_BG, foreground_color=COLOR_TEXT_MAIN, cursor_color=COLOR_ORANGE, size_hint_y=None, height=40)
        inputs_box.add_widget(self.txt_act)

        # حد دوز
        lbl_dose = Label(text=fa("حد دوز مجاز طناب‌کشی (μSv/h):"), font_name=FONT_NAME, font_size='13sp', color=COLOR_TEXT_MAIN, size_hint_y=None, height=22, halign='right')
        lbl_dose.bind(size=lbl_dose.setter('text_size'))
        inputs_box.add_widget(lbl_dose)
        self.txt_dose = TextInput(text="2.5", multiline=False, font_size='15sp', background_color=COLOR_INPUT_BG, foreground_color=COLOR_TEXT_MAIN, cursor_color=COLOR_ORANGE, size_hint_y=None, height=40)
        inputs_box.add_widget(self.txt_dose)

        main_layout.add_widget(inputs_box)

        # 5. دکمه محاسبه
        calc_btn = Button(
            text=fa("محاسبه حریم کنترل‌شده"),
            font_name=FONT_NAME,
            font_size='16sp',
            bold=True,
            background_normal='',
            background_color=COLOR_ORANGE,
            color=COLOR_BG,
            size_hint_y=None,
            height=50
        )
        calc_btn.bind(on_release=self.calculate)
        main_layout.add_widget(calc_btn)

        # 6. کارت نمایش نتایج
        result_box = BoxLayout(orientation='vertical', padding=14, spacing=6, size_hint_y=None, height=130)
        with result_box.canvas.before:
            Color(*COLOR_CARD)
            self.rect_res = RoundedRectangle(size=result_box.size, pos=result_box.pos, radius=[10])
        result_box.bind(pos=lambda obj, val: setattr(self.rect_res, 'pos', val),
                        size=lambda obj, val: setattr(self.rect_res, 'size', val))

        res_title = Label(text=fa("فاصله ایمن طناب‌کشی (شعاع):"), font_name=FONT_NAME, font_size='14sp', color=COLOR_MUTED)
        self.res_val = Label(text="-- متر", font_name=FONT_NAME, font_size='26sp', bold=True, color=COLOR_ORANGE)
        self.res_sub = Label(text=fa("جهت اعمال قانون عکس مجذور فاصله"), font_name=FONT_NAME, font_size='12sp', color=COLOR_MUTED)

        result_box.add_widget(res_title)
        result_box.add_widget(self.res_val)
        result_box.add_widget(self.res_sub)
        main_layout.add_widget(result_box)

        root_scroll.add_widget(main_layout)
        return root_scroll

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
            self.res_sub.text = fa(f"ایزوتوپ: {self.selected_iso} | گاما: {gamma}")
        except Exception:
            self.res_val.text = fa("خطا در ورودی")
            self.res_sub.text = fa("لطفاً اعداد معتبر انگلیسی وارد کنید")

if __name__ == '__main__':
    NDTCalculatorApp().run()
