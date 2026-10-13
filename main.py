# -*- coding: utf-8 -*-
"""
NDT Gamma Pro - Industrial Gamma Radiography Safety Calculator
Design 5: Industrial High-Contrast Dark Mode (Default)
"""
from __future__ import annotations

import math
import os
from typing import Dict, List, Optional

# پشتیبانی راست‌به‌چپ (RTL) به همراه حالت فال‌بک
try:
    import arabic_reshaper
    from bidi.algorithm import get_display

    def fa(text: str) -> str:
        if not text:
            return ""
        try:
            return get_display(arabic_reshaper.reshape(text))
        except Exception:
            return text
except Exception:
    def fa(text: str) -> str:
        return text


def _fmt(val: float, nd: int = 2) -> str:
    if val is None or math.isnan(val) or math.isinf(val):
        return "-"
    if abs(val) >= 1000:
        return f"{val:,.1f}"
    if abs(val) >= 10:
        return f"{val:.1f}"
    if abs(val) >= 1:
        return f"{val:.2f}"
    return f"{val:.{nd}f}"


def fa_num(value, nd: int = 3) -> str:
    try:
        return fa(_fmt(float(value), nd=nd))
    except Exception:
        return fa(str(value))


# ثوابت ایزوتوپ‌های پرتوزا
ISOTOPES = {
    "Ir-192": {
        "name": "Iridium-192",
        "half_life": 73.83,
        "gamma_constant": 130.0,
        "hvl_steel": 13.0,
    },
    "Se-75": {
        "name": "Selenium-75",
        "half_life": 119.8,
        "gamma_constant": 54.0,
        "hvl_steel": 8.0,
    },
    "Co-60": {
        "name": "Cobalt-60",
        "half_life": 1925.0,
        "gamma_constant": 351.0,
        "hvl_steel": 22.0,
    },
    "Cs-137": {
        "name": "Cesium-137",
        "half_life": 11000.0,
        "gamma_constant": 89.0,
        "hvl_steel": 16.0,
    },
}

# پالت رنگی طرح ۵ (حالت تیره صنعتی)
DARK_THEME = {
    "bg": (0.07, 0.08, 0.09, 1),           # #121416
    "card": (0.12, 0.14, 0.16, 1),         # #1F2327
    "card_border": (0.18, 0.20, 0.23, 1),  # #2E343A
    "primary": (1.0, 0.48, 0.0, 1),        # نارنجی ایمنی صنعتی #FF7A00
    "accent": (0.06, 0.49, 0.54, 1),       # سبز-آبی صنعتی
    "text": (0.95, 0.96, 0.97, 1),         # شیری / سفید پرنور
    "subtext": (0.61, 0.64, 0.69, 1),      # خاکستری ملایم
    "warning": (1.0, 0.40, 0.0, 1),        # بنر هشدار
}

from kivy.app import App
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.button import Button
from kivy.graphics import Color, RoundedRectangle, Line


class DarkCard(BoxLayout):
    """کارت تیره با حاشیه صنعتی و گوشه‌های گرد"""
    def __init__(self, border_color=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = 12
        self.spacing = 8
        self.border_c = border_color or DARK_THEME["card_border"]
        self.bind(pos=self._update_bg, size=self._update_bg)

    def _update_bg(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*DARK_THEME["card"])
            RoundedRectangle(pos=self.pos, size=self.size, radius=[10])
            Color(*self.border_c)
            Line(rounded_rectangle=(self.pos[0], self.pos[1], self.size[0], self.size[1], 10), width=1.1)


class NDTGammaApp(App):
    def build(self):
        Window.clearcolor = DARK_THEME["bg"]
        self.title = "NDT Gamma Pro - Industrial Dark"

        root_scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        layout = BoxLayout(orientation="vertical", padding=14, spacing=12, size_hint_y=None)
        layout.bind(minimum_height=layout.setter("height"))

        # نوار بالایی تیره صنعتی
        top_bar = DarkCard(size_hint_y=None, height=65, border_color=DARK_THEME["primary"])
        title = Label(
            text=fa("محاسبه‌گر ایمنی پرتوی گاما (NDT)"),
            font_size="18sp",
            bold=True,
            color=DARK_THEME["primary"],
        )
        top_bar.add_widget(title)
        layout.add_widget(top_bar)

        # بنر هشدار ایمنی صنعتی
        alert_box = DarkCard(size_hint_y=None, height=75, border_color=DARK_THEME["warning"])
        alert_title = Label(
            text=fa("هشدار ایمنی پرتویی: همیشه از دوزیمتر فردی و تجهیزات کالیبره‌شده استفاده کنید."),
            font_size="13sp",
            color=DARK_THEME["warning"],
            halign="center",
        )
        alert_title.bind(size=alert_title.setter("text_size"))
        alert_box.add_widget(alert_title)
        layout.add_widget(alert_box)

        # پنل ورودی داده‌ها
        form_card = DarkCard(size_hint_y=None, height=330)
        
        # انتخابگر ایزوتوپ
        form_card.add_widget(Label(text=fa("انتخاب ایزوتوپ پرتوزا:"), color=DARK_THEME["text"], size_hint_y=None, height=24))
        self.iso_spinner = Spinner(
            text="Ir-192",
            values=tuple(ISOTOPES.keys()),
            size_hint_y=None,
            height=44,
            background_color=DARK_THEME["accent"],
            color=DARK_THEME["text"],
        )
        form_card.add_widget(self.iso_spinner)

        # اکتیویته اولیه
        form_card.add_widget(Label(text=fa("اکتیویته اولیه چشمه (GBq):"), color=DARK_THEME["text"], size_hint_y=None, height=24))
        self.act_input = TextInput(text="1850", multiline=False, input_filter="float", size_hint_y=None, height=40,
                                   background_color=(0.18, 0.2, 0.22, 1), foreground_color=DARK_THEME["text"])
        form_card.add_widget(self.act_input)

        # روزهای سپری‌شده
        form_card.add_widget(Label(text=fa("روزهای سپری‌شده:"), color=DARK_THEME["text"], size_hint_y=None, height=24))
        self.days_input = TextInput(text="30", multiline=False, input_filter="float", size_hint_y=None, height=40,
                                    background_color=(0.18, 0.2, 0.22, 1), foreground_color=DARK_THEME["text"])
        form_card.add_widget(self.days_input)

        # حد مجاز دوز جهت طناب‌کشی
        form_card.add_widget(Label(text=fa("حد مجاز دوز طناب‌کشی (uSv/h):"), color=DARK_THEME["text"], size_hint_y=None, height=24))
        self.dose_limit_input = TextInput(text="2.5", multiline=False, input_filter="float", size_hint_y=None, height=40,
                                          background_color=(0.18, 0.2, 0.22, 1), foreground_color=DARK_THEME["text"])
        form_card.add_widget(self.dose_limit_input)

        layout.add_widget(form_card)

        # دکمه محاسبه نارنجی با استایل کارگاهی
        calc_btn = Button(
            text=fa("محاسبه فاصله ایمن و اکتیویته"),
            size_hint_y=None,
            height=50,
            background_color=DARK_THEME["primary"],
            color=(0.05, 0.05, 0.05, 1),
            bold=True,
            font_size="16sp",
        )
        calc_btn.bind(on_press=self.calculate)
        layout.add_widget(calc_btn)

        # کارت بزرگ نتیجه (هایلایت صنعتی نارنجی)
        self.res_card = DarkCard(size_hint_y=None, height=180, border_color=DARK_THEME["primary"])
        self.res_title = Label(
            text=fa("فاصله ایمن پیشنهادی (طناب‌کشی)"),
            font_size="15sp",
            color=DARK_THEME["subtext"],
            size_hint_y=None,
            height=25,
        )
        self.res_distance = Label(
            text=fa("0.0 متر"),
            font_size="32sp",
            bold=True,
            color=DARK_THEME["primary"],
            size_hint_y=None,
            height=50,
        )
        self.res_details = Label(
            text=fa("اکتیویته کنونی: - | نرخ دوز در ۱ متر: -"),
            font_size="13sp",
            color=DARK_THEME["text"],
            halign="center",
        )
        self.res_details.bind(size=self.res_details.setter("text_size"))
        self.res_card.add_widget(self.res_title)
        self.res_card.add_widget(self.res_distance)
        self.res_card.add_widget(self.res_details)
        layout.add_widget(self.res_card)

        root_scroll.add_widget(layout)
        return root_scroll

    def calculate(self, instance):
        try:
            iso_key = self.iso_spinner.text
            iso = ISOTOPES[iso_key]
            a0 = float(self.act_input.text or 0)
            days = float(self.days_input.text or 0)
            limit = float(self.dose_limit_input.text or 2.5)

            # محاسبات فیزیکی افت اکتیویته و دوز
            t_half = iso["half_life"]
            current_act = a0 * (0.5 ** (days / t_half))
            gamma_c = iso["gamma_constant"]
            dose_at_1m = current_act * gamma_c

            if limit <= 0:
                limit = 2.5
            safe_dist = math.sqrt(dose_at_1m / limit)

            self.res_distance.text = f"{fa_num(safe_dist, nd=2)} " + fa("متر")
            details_str = (
                f"اکتیویته فعلی: {fa_num(current_act, nd=1)} GBq\n"
                f"آهنگ دوز در ۱ متر: {fa_num(dose_at_1m, nd=0)} uSv/h"
            )
            self.res_details.text = fa(details_str)
        except Exception as err:
            self.res_details.text = fa(f"خطا در ورودی‌ها: {str(err)}")


if __name__ == "__main__":
    NDTGammaApp().run()
