# -*- coding: utf-8 -*-
import math
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.modalview import ModalView
from kivy.graphics import Color, RoundedRectangle, Line

# ماژول‌های اصلاح متن و چیدمان راست‌به‌چپ فارسی
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

# مقادیر ثابت پرتودهی گاما بر حسب (R * m^2 / (hr * Ci))
ISOTOPES = {
    "Ir-192": {"name": "Ir-192", "gamma": 0.48, "fa_name": "ایریدیوم ۱۹۲"},
    "Se-75":  {"name": "Se-75",  "gamma": 0.20, "fa_name": "سلنیوم ۷۵"},
    "Co-60":  {"name": "Co-60",  "gamma": 1.32, "fa_name": "کبالت ۶۰"},
    "Cs-137": {"name": "Cs-137", "gamma": 0.33, "fa_name": "سزیوم ۱۳۷"}
}

COMPANY_PHONES = ["09122012248", "09121042253", "09121326011"]


class RoundedCard(BoxLayout):
    """ویجت کارت مدرن تیره با لبه‌های منحنی و کادر مرزی دقیق"""
    def __init__(self, bg_color=(0.11, 0.13, 0.16, 1), border_color=(0.20, 0.25, 0.30, 1), radius=16, **kwargs):
        super(RoundedCard, self).__init__(**kwargs)
        self.bg_color = bg_color
        self.border_color = border_color
        self.radius = radius
        with self.canvas.before:
            self.color_bg = Color(*self.bg_color)
            self.rect_bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[self.radius])
            self.color_line = Color(*self.border_color)
            self.line_border = Line(rounded_rectangle=[self.x, self.y, self.width, self.height, self.radius], width=1.4)
        self.bind(pos=self._update_shape, size=self._update_shape)

    def _update_shape(self, *args):
        self.rect_bg.pos = self.pos
        self.rect_bg.size = self.size
        self.line_border.rounded_rectangle = [self.x, self.y, self.width, self.height, self.radius]


class NDTCalculatorApp(App):
    def build(self):
        Window.clearcolor = (0.07, 0.08, 0.09, 1)  # پس‌زمینه زغالی ایمنی
        self.selected_isotope = "Ir-192"
        self.iso_buttons = {}

        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True)
        root = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            padding=[20, 16, 20, 24],
            spacing=16
        )
        root.bind(minimum_height=root.setter('height'))

        # ----------------- ۱. سربرگ و لوگوی شرکت -----------------
        header_box = BoxLayout(orientation='vertical', size_hint_y=None, height=160, spacing=6)
        
        try:
            logo_img = Image(source='logo.png', size_hint=(None, None), size=(84, 84), pos_hint={'center_x': 0.5})
            header_box.add_widget(logo_img)
        except Exception:
            pass

        title_lbl = Label(
            text=fa("محاسبه‌گر فاصله ایمن رادیوگرافی"),
            font_name=FONT_PATH,
            font_size='21sp',
            bold=True,
            color=(0.95, 0.95, 0.98, 1),
            size_hint_y=None,
            height=36
        )
        company_btn = Button(
            text=fa("شرکت رادیوگرافی صنعتی ایران  [ تماس مستقیم ]"),
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

        # ----------------- ۲. نوار ایمنی و اخطار پرتوی -----------------
        warning_banner = RoundedCard(
            bg_color=(1.0, 0.46, 0.0, 0.95),
            border_color=(1.0, 0.62, 0.2, 1),
            radius=12,
            size_hint_y=None,
            height=48,
            padding=[10, 6]
        )
        warn_lbl = Label(
            text=fa("⚠  هشدار ایمنی: رعایت حریم کنترل‌شده اشعه الزامی است  ⚠"),
            font_name=FONT_PATH,
            font_size='13sp',
            bold=True,
            color=(0.06, 0.06, 0.06, 1)
        )
        warning_banner.add_widget(warn_lbl)
        root.add_widget(warning_banner)

        # ----------------- ۳. انتخاب ایزوتوپ صنعتی -----------------
        iso_card = RoundedCard(
            orientation='vertical',
            size_hint_y=None,
            height=112,
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

        # ----------------- ۴. ورودی‌های اکتیویته و حد دوز مجاز -----------------
        inputs_row = BoxLayout(spacing=12, size_hint_y=None, height=116)

        # اکتیویته چشمه (Ci)
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
            background_color=(0.08, 0.10, 0.12, 1),
            foreground_color=(1, 1, 1, 1),
            cursor_color=(1, 0.5, 0, 1),
            padding=[10, 12]
        )
        self.input_activity.bind(text=self.calculate)
        card_act.add_widget(self.input_activity)

        # حد دوز مجاز (µSv/h)
        card_dose = RoundedCard(orientation='vertical', padding=[12, 10], spacing=8)
        card_dose.add_widget(Label(
            text=fa("حد دوز مجاز (µSv/h)"),
            font_name=FONT_PATH,
            font_size='14sp',
            bold=True,
            color=(0.85, 0.88, 0.92, 1),
            size_hint_y=None,
            height=22
        ))
        self.input_dose = TextInput(
            text="7.5",
            multiline=False,
            input_filter='float',
            font_size='20sp',
            halign='center',
            background_normal='',
            background_color=(0.08, 0.10, 0.12, 1),
            foreground_color=(1, 1, 1, 1),
            cursor_color=(1, 0.5, 0, 1),
            padding=[10, 12]
        )
        self.input_dose.bind(text=self.calculate)
        card_dose.add_widget(self.input_dose)

        inputs_row.add_widget(card_act)
        inputs_row.add_widget(card_dose)
        root.add_widget(inputs_row)

        # ----------------- ۵. دکمه محاسبه فاصله ایمن -----------------
        calc_btn = Button(
            text=fa("محاسبه فاصله ایمن مرزبندی"),
            font_name=FONT_PATH,
            font_size='18sp',
            bold=True,
            size_hint_y=None,
            height=58,
            background_normal='',
            background_color=(1.0, 0.48, 0.0, 1),
            color=(0.08, 0.08, 0.08, 1)
        )
        calc_btn.bind(on_release=self.calculate)
        root.add_widget(calc_btn)

        # ----------------- ۶. کارت بزرگ سبز نمایش نتیجه -----------------
        self.result_card = RoundedCard(
            orientation='vertical',
            bg_color=(0.04, 0.18, 0.12, 0.95),
            border_color=(0.1, 0.85, 0.48, 1),
            radius=16,
            size_hint_y=None,
            height=140,
            padding=[16, 14],
            spacing=6
        )
        
        self.lbl_res_title = Label(
            text=fa("فاصله ایمن مرزبندی طناب‌کشی"),
            font_name=FONT_PATH,
            font_size='16sp',
            bold=True,
            color=(0.7, 0.95, 0.8, 1),
            size_hint_y=None,
            height=26
        )
        self.lbl_res_value = Label(
            text=fa("--- متر"),
            font_name=FONT_PATH,
            font_size='38sp',
            bold=True,
            color=(0.15, 0.98, 0.55, 1),
            size_hint_y=None,
            height=54
        )
        self.lbl_res_detail = Label(
            text=fa("آماده برای محاسبه..."),
            font_name=FONT_PATH,
            font_size='13sp',
            color=(0.6, 0.8, 0.7, 1),
            size_hint_y=None,
            height=24
        )

        self.result_card.add_widget(self.lbl_res_title)
        self.result_card.add_widget(self.lbl_res_value)
        self.result_card.add_widget(self.lbl_res_detail)
        root.add_widget(self.result_card)

        scroll.add_widget(root)
        self.calculate()
        return scroll

    def select_isotope(self, key):
        self.selected_isotope = key
        for k, btn in self.iso_buttons.items():
            if k == key:
                btn.background_color = (1.0, 0.48, 0.0, 1)
                btn.color = (1, 1, 1, 1)
            else:
                btn.background_color = (0.16, 0.19, 0.23, 1)
                btn.color = (0.8, 0.8, 0.8, 1)
        self.calculate()

    def calculate(self, *args):
        try:
            A = float(self.input_activity.text)
            dose_uSv = float(self.input_dose.text)
            if A <= 0 or dose_uSv <= 0:
                raise ValueError()

            # رابطه قانون عکس مجذور فاصله: Dose_Rate (R/h) = (Gamma * A) / d^2
            # تبدیل حد دوز: 1 R/h = 10,000 µSv/h  =>  Dose(R/h) = dose_uSv / 10000
            # d = sqrt((Gamma * A) / Dose(R/h))
            gamma = ISOTOPES[self.selected_isotope]["gamma"]
            dose_R_hr = dose_uSv / 10000.0
            distance_m = math.sqrt((gamma * A) / dose_R_hr)

            self.lbl_res_value.text = fa(f"{distance_m:.1f} متر")
            self.lbl_res_detail.text = fa(f"ایزوتوپ: {self.selected_isotope} | اکتیویته: {A} Ci | حد دوز: {dose_uSv} µSv/h")
        except Exception:
            self.lbl_res_value.text = fa("خطا در ورودی")
            self.lbl_res_detail.text = fa("لطفاً اعداد معتبر وارد کنید")

    def show_contact_modal(self, *args):
        modal = ModalView(size_hint=(0.9, 0.58), auto_dismiss=True)
        layout = RoundedCard(
            orientation='vertical',
            bg_color=(0.10, 0.12, 0.15, 0.98),
            border_color=(1.0, 0.48, 0.0, 1),
            padding=[20, 20],
            spacing=12
        )
        
        layout.add_widget(Label(
            text=fa("شرکت رادیوگرافی صنعتی ایران"),
            font_name=FONT_PATH,
            font_size='18sp',
            bold=True,
            color=(1.0, 0.55, 0.1, 1),
            size_hint_y=None,
            height=30
        ))
        layout.add_widget(Label(
            text=fa("مرجع تخصصی خدمات NDT و آزمون‌های غیرمخرب"),
            font_name=FONT_PATH,
            font_size='13sp',
            color=(0.8, 0.85, 0.9, 1),
            size_hint_y=None,
            height=24
        ))
        
        for p in COMPANY_PHONES:
            layout.add_widget(Label(
                text=f"📞  {p}",
                font_size='16sp',
                bold=True,
                color=(0.2, 0.9, 0.5, 1),
                size_hint_y=None,
                height=28
            ))

        close_btn = Button(
            text=fa("بستن صفحه"),
            font_name=FONT_PATH,
            font_size='15sp',
            bold=True,
            size_hint_y=None,
            height=46,
            background_normal='',
            background_color=(0.25, 0.30, 0.35, 1)
        )
        close_btn.bind(on_release=modal.dismiss)
        layout.add_widget(close_btn)

        modal.add_widget(layout)
        modal.open()


if __name__ == '__main__':
    NDTCalculatorApp().run()
