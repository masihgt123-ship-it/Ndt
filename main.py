# -*- coding: utf-8 -*-
"""
Industrial Gamma Radiography (NDT) Multi-Tool App
شرکت رادیوگرافی صنعتی ایران
"""
import math
import os
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

FONT_PATH = "font.ttf" if os.path.exists("font.ttf") else "Roboto"

# مشخصات ایزوتوپ‌های صنعتی
ISOTOPES = {
    "Ir-192": {
        "name": "Ir-192",
        "fa_name": "ایریدیوم ۱۹۲",
        "gamma": 0.48,           # R * m^2 / (hr * Ci)
        "half_life_days": 73.83,
        "hvl_lead_mm": 5.0,
        "hvl_steel_mm": 13.0,
        "energy_range": "300 - 600 keV"
    },
    "Se-75": {
        "name": "Se-75",
        "fa_name": "سلنیوم ۷۵",
        "gamma": 0.20,
        "half_life_days": 119.8,
        "hvl_lead_mm": 2.5,
        "hvl_steel_mm": 8.0,
        "energy_range": "66 - 400 keV"
    },
    "Co-60": {
        "name": "Co-60",
        "fa_name": "کبالت ۶۰",
        "gamma": 1.32,
        "half_life_days": 1925.0,
        "hvl_lead_mm": 12.5,
        "hvl_steel_mm": 22.0,
        "energy_range": "1.17 - 1.33 MeV"
    },
    "Cs-137": {
        "name": "Cs-137",
        "fa_name": "سزیوم ۱۳۷",
        "gamma": 0.33,
        "half_life_days": 11000.0,
        "hvl_lead_mm": 6.5,
        "hvl_steel_mm": 16.0,
        "energy_range": "662 keV"
    }
}

COMPANY_PHONES = ["09122012248", "09121042253", "09121326011"]


class RoundedCard(BoxLayout):
    def __init__(self, bg_color=(0.09, 0.11, 0.13, 1), border_color=(0.20, 0.24, 0.28, 1), radius=14, **kwargs):
        super(RoundedCard, self).__init__(**kwargs)
        self.bg_color = bg_color
        self.border_color = border_color
        self.radius = radius
        with self.canvas.before:
            self.color_bg = Color(*self.bg_color)
            self.rect_bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[self.radius])
            self.color_line = Color(*self.border_color)
            self.line_border = Line(rounded_rectangle=[self.x, self.y, self.width, self.height, self.radius], width=1.2)
        self.bind(pos=self._update_shape, size=self._update_shape)

    def _update_shape(self, *args):
        self.rect_bg.pos = self.pos
        self.rect_bg.size = self.size
        self.line_border.rounded_rectangle = [self.x, self.y, self.width, self.height, self.radius]


class NDTApp(App):
    def build(self):
        Window.clearcolor = (0.06, 0.07, 0.08, 1)
        self.current_isotope = "Ir-192"

        # ساختار ریشه: عمودی (سربرگ + فضای تب‌ها + نوار ناوبری پایین)
        self.root_layout = BoxLayout(orientation='vertical')

        # ۱. سربرگ مشترک (Header)
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=64, padding=[16, 8, 16, 8], spacing=10)
        with header.canvas.before:
            Color(0.09, 0.11, 0.13, 1)
            self.header_bg = RoundedRectangle(pos=header.pos, size=header.size)
        header.bind(pos=lambda *a: setattr(self.header_bg, 'pos', header.pos),
                    size=lambda *a: setattr(self.header_bg, 'size', header.size))

        header_title = Label(
            text=fa("جعبه‌ابزار تخصصی رادیوگرافی صنعتی NDT"),
            font_name=FONT_PATH,
            font_size='16sp',
            bold=True,
            color=(1, 0.60, 0.05, 1),
            halign='right',
            valign='middle'
        )
        header_title.bind(size=header_title.setter('text_size'))
        header.add_widget(header_title)
        self.root_layout.add_widget(header)

        # ۲. پنل محتوای متغیر
        self.content_area = BoxLayout(orientation='vertical', size_hint=(1, 1))
        self.root_layout.add_widget(self.content_area)

        # ۳. نوار ناوبری پایین (Bottom Navigation Bar)
        nav_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=62, spacing=4, padding=[6, 6, 6, 6])
        with nav_bar.canvas.before:
            Color(0.09, 0.10, 0.12, 1)
            self.nav_bg = RoundedRectangle(pos=nav_bar.pos, size=nav_bar.size)
        nav_bar.bind(pos=lambda *a: setattr(self.nav_bg, 'pos', nav_bar.pos),
                     size=lambda *a: setattr(self.nav_bg, 'size', nav_bar.size))

        self.nav_buttons = {}
        tabs = [
            ("distance", fa("مرزبندی و حفاظ")),
            ("decay", fa("واپاشی روز")),
            ("exposure", fa("زمان پرتودهی")),
            ("specs", fa("ایزوتوپ‌ها و تماس"))
        ]

        for tab_id, tab_label in tabs:
            btn = Button(
                text=tab_label,
                font_name=FONT_PATH,
                font_size='12sp',
                bold=True,
                background_normal='',
                background_color=(0.14, 0.17, 0.20, 1),
                color=(0.85, 0.85, 0.9, 1)
            )
            btn.bind(on_release=lambda inst, t=tab_id: self.switch_tab(t))
            self.nav_buttons[tab_id] = btn
            nav_bar.add_widget(btn)

        self.root_layout.add_widget(nav_bar)

        # شروع برنامه روی تب اول
        self.switch_tab("distance")
        return self.root_layout

    def switch_tab(self, tab_id):
        # استایل دکمه‌های ناوبری
        for tid, btn in self.nav_buttons.items():
            if tid == tab_id:
                btn.background_color = (1.0, 0.48, 0.0, 1)
                btn.color = (0.05, 0.05, 0.05, 1)
            else:
                btn.background_color = (0.13, 0.15, 0.18, 1)
                btn.color = (0.75, 0.80, 0.85, 1)

        self.content_area.clear_widgets()

        if tab_id == "distance":
            self.content_area.add_widget(self.build_distance_tab())
        elif tab_id == "decay":
            self.content_area.add_widget(self.build_decay_tab())
        elif tab_id == "exposure":
            self.content_area.add_widget(self.build_exposure_tab())
        elif tab_id == "specs":
            self.content_area.add_widget(self.build_specs_tab())

    # ========================== تب ۱: مرزبندی و حفاظ ==========================
    def build_distance_tab(self):
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        box = BoxLayout(orientation='vertical', size_hint_y=None, padding=[16, 12, 16, 20], spacing=12)
        box.bind(minimum_height=box.setter('height'))

        # انتخاب ایزوتوپ
        iso_card = RoundedCard(orientation='vertical', size_hint_y=None, height=92, padding=[10, 8], spacing=6)
        iso_card.add_widget(Label(text=fa("انتخاب ایزوتوپ فعال"), font_name=FONT_PATH, font_size='13sp', color=(0.8, 0.85, 0.9, 1)))
        grid = GridLayout(cols=4, spacing=6, size_hint_y=None, height=42)
        self.dist_iso_btns = {}
        for k in ["Ir-192", "Se-75", "Co-60", "Cs-137"]:
            b = Button(
                text=k,
                font_size='14sp',
                bold=True,
                background_normal='',
                background_color=(1.0, 0.48, 0.0, 1) if k == self.current_isotope else (0.15, 0.18, 0.22, 1),
                color=(1, 1, 1, 1)
            )
            b.bind(on_release=lambda inst, key=k: self.set_isotope(key))
            self.dist_iso_btns[k] = b
            grid.add_widget(b)
        iso_card.add_widget(grid)
        box.add_widget(iso_card)

        # ورودی اکتیویته و حد دوز
        inputs_row = BoxLayout(spacing=10, size_hint_y=None, height=96)

        c1 = RoundedCard(orientation='vertical', padding=[8, 6], spacing=4)
        c1.add_widget(Label(text=fa("اکتیویته (Ci)"), font_name=FONT_PATH, font_size='13sp', color=(0.8, 0.85, 0.9, 1)))
        self.txt_dist_act = TextInput(text="40", multiline=False, input_filter='float', font_size='18sp', halign='center',
                                      background_color=(0.14, 0.17, 0.20, 1), foreground_color=(1, 1, 1, 1))
        self.txt_dist_act.bind(text=self.calc_distance)
        c1.add_widget(self.txt_dist_act)

        c2 = RoundedCard(orientation='vertical', padding=[8, 6], spacing=4)
        c2.add_widget(Label(text=fa("حد دوز (µSv/h)"), font_name=FONT_PATH, font_size='13sp', color=(0.8, 0.85, 0.9, 1)))
        self.txt_dist_limit = TextInput(text="7.5", multiline=False, input_filter='float', font_size='18sp', halign='center',
                                        background_color=(0.14, 0.17, 0.20, 1), foreground_color=(1, 1, 1, 1))
        self.txt_dist_limit.bind(text=self.calc_distance)
        c2.add_widget(self.txt_dist_limit)

        inputs_row.add_widget(c1)
        inputs_row.add_widget(c2)
        box.add_widget(inputs_row)

        # ورودی حفاظ سربی (HVL)
        c_shield = RoundedCard(orientation='vertical', size_hint_y=None, height=96, padding=[10, 8], spacing=4)
        c_shield.add_widget(Label(text=fa("ضخامت حفاظ سربی یا کلیماتور (میلی‌متر)"), font_name=FONT_PATH, font_size='13sp', color=(0.8, 0.85, 0.9, 1)))
        self.txt_lead_shield = TextInput(text="0", multiline=False, input_filter='float', font_size='18sp', halign='center',
                                         background_color=(0.14, 0.17, 0.20, 1), foreground_color=(1, 1, 1, 1))
        self.txt_lead_shield.bind(text=self.calc_distance)
        c_shield.add_widget(self.txt_lead_shield)
        box.add_widget(c_shield)

        # کارت نتیجه
        self.card_dist_res = RoundedCard(
            orientation='vertical',
            bg_color=(0.04, 0.18, 0.12, 0.95),
            border_color=(0.15, 0.85, 0.50, 1),
            size_hint_y=None,
            height=130,
            padding=[12, 10],
            spacing=4
        )
        self.lbl_dist_val = Label(text=fa("--- متر"), font_name=FONT_PATH, font_size='34sp', bold=True, color=(0.2, 0.98, 0.55, 1))
        self.lbl_dist_sub = Label(text="", font_name=FONT_PATH, font_size='13sp', color=(0.7, 0.85, 0.8, 1))
        self.card_dist_res.add_widget(Label(text=fa("شعاع فاصله ایمن مرزبندی طناب‌کشی"), font_name=FONT_PATH, font_size='14sp', color=(0.8, 0.95, 0.85, 1)))
        self.card_dist_res.add_widget(self.lbl_dist_val)
        self.card_dist_res.add_widget(self.lbl_dist_sub)
        box.add_widget(self.card_dist_res)

        scroll.add_widget(box)
        self.calc_distance()
        return scroll

    def set_isotope(self, key):
        self.current_isotope = key
        for k, btn in getattr(self, 'dist_iso_btns', {}).items():
            btn.background_color = (1.0, 0.48, 0.0, 1) if k == key else (0.15, 0.18, 0.22, 1)
        self.calc_distance()

    def calc_distance(self, *args):
        try:
            A = float(self.txt_dist_act.text)
            dose_uSv = float(self.txt_dist_limit.text)
            shield_mm = float(self.txt_lead_shield.text) if self.txt_lead_shield.text else 0.0
            if A <= 0 or dose_uSv <= 0:
                raise ValueError()

            iso = ISOTOPES[self.current_isotope]
            gamma = iso["gamma"]
            hvl = iso["hvl_lead_mm"]

            # محاسبه تضعیف با حفاظ
            att_factor = 0.5 ** (shield_mm / hvl) if shield_mm > 0 else 1.0
            eff_activity = A * att_factor

            # فرمول دقیق فاصله استاندارد NDT
            # d = sqrt( (Gamma * Eff_Activity * 10000) / Dose_uSv )
            dose_R_hr = dose_uSv / 10000.0
            d = math.sqrt((gamma * eff_activity) / dose_R_hr)

            self.lbl_dist_val.text = fa(f"{d:.1f} متر")
            if shield_mm > 0:
                self.lbl_dist_sub.text = fa(f"با {shield_mm}mm سرب | اکتیویته مؤثر: {eff_activity:.2f} Ci")
            else:
                self.lbl_dist_sub.text = fa(f"بدون حفاظ | ثابت گاما: {gamma}")
        except Exception:
            self.lbl_dist_val.text = fa("خطا در ورودی")
            self.lbl_dist_sub.text = fa("لطفاً مقادیر را به درستی وارد کنید")

    # ========================== تب ۲: واپاشی و اکتیویته روز ==========================
    def build_decay_tab(self):
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        box = BoxLayout(orientation='vertical', size_hint_y=None, padding=[16, 12, 16, 20], spacing=12)
        box.bind(minimum_height=box.setter('height'))

        # انتخاب ایزوتوپ
        c_iso = RoundedCard(orientation='vertical', size_hint_y=None, height=90, padding=[10, 6], spacing=6)
        c_iso.add_widget(Label(text=fa("ایزوتوپ مورد نظر"), font_name=FONT_PATH, font_size='13sp', color=(0.8, 0.85, 0.9, 1)))
        g = GridLayout(cols=4, spacing=6, size_hint_y=None, height=42)
        self.decay_iso_btns = {}
        for k in ["Ir-192", "Se-75", "Co-60", "Cs-137"]:
            b = Button(
                text=k,
                font_size='14sp',
                bold=True,
                background_normal='',
                background_color=(1.0, 0.48, 0.0, 1) if k == self.current_isotope else (0.15, 0.18, 0.22, 1)
            )
            b.bind(on_release=lambda inst, key=k: self.set_decay_iso(key))
            self.decay_iso_btns[k] = b
            g.add_widget(b)
        c_iso.add_widget(g)
        box.add_widget(c_iso)

        # ورودی‌ها
        r = BoxLayout(spacing=10, size_hint_y=None, height=96)
        c1 = RoundedCard(orientation='vertical', padding=[8, 6], spacing=4)
        c1.add_widget(Label(text=fa("اکتیویته اولیه (Ci)"), font_name=FONT_PATH, font_size='13sp', color=(0.8, 0.85, 0.9, 1)))
        self.txt_decay_a0 = TextInput(text="80", multiline=False, input_filter='float', font_size='18sp', halign='center',
                                      background_color=(0.14, 0.17, 0.20, 1), foreground_color=(1, 1, 1, 1))
        self.txt_decay_a0.bind(text=self.calc_decay)
        c1.add_widget(self.txt_decay_a0)

        c2 = RoundedCard(orientation='vertical', padding=[8, 6], spacing=4)
        c2.add_widget(Label(text=fa("روزهای گذشته"), font_name=FONT_PATH, font_size='13sp', color=(0.8, 0.85, 0.9, 1)))
        self.txt_decay_days = TextInput(text="45", multiline=False, input_filter='float', font_size='18sp', halign='center',
                                        background_color=(0.14, 0.17, 0.20, 1), foreground_color=(1, 1, 1, 1))
        self.txt_decay_days.bind(text=self.calc_decay)
        c2.add_widget(self.txt_decay_days)
        r.add_widget(c1)
        r.add_widget(c2)
        box.add_widget(r)

        # کارت نتیجه اکتیویته روز
        c_res = RoundedCard(orientation='vertical', bg_color=(0.05, 0.15, 0.22, 0.95), border_color=(0.2, 0.6, 0.9, 1),
                            size_hint_y=None, height=140, padding=[12, 10], spacing=4)
        c_res.add_widget(Label(text=fa("اکتیویته دقیق روز جاری"), font_name=FONT_PATH, font_size='14sp', color=(0.7, 0.9, 1, 1)))
        self.lbl_decay_val = Label(text="--- Ci", font_name=FONT_PATH, font_size='34sp', bold=True, color=(0.3, 0.8, 1, 1))
        self.lbl_decay_sub = Label(text="", font_name=FONT_PATH, font_size='13sp', color=(0.7, 0.85, 0.9, 1))
        c_res.add_widget(self.lbl_decay_val)
        c_res.add_widget(self.lbl_decay_sub)
        box.add_widget(c_res)

        # پیش‌بینی ۷ روز آینده
        self.box_forecast = RoundedCard(orientation='vertical', size_hint_y=None, height=190, padding=[12, 10], spacing=4)
        self.box_forecast.add_widget(Label(text=fa("پیش‌بینی اکتیویته ۷ روز آینده (پلاک روزانه)"), font_name=FONT_PATH, font_size='13sp', bold=True, color=(1, 0.7, 0.2, 1)))
        self.lbl_forecast_text = Label(text="", font_name=FONT_PATH, font_size='12sp', color=(0.85, 0.85, 0.85, 1))
        self.box_forecast.add_widget(self.lbl_forecast_text)
        box.add_widget(self.box_forecast)

        scroll.add_widget(box)
        self.calc_decay()
        return scroll

    def set_decay_iso(self, key):
        self.current_isotope = key
        for k, btn in getattr(self, 'decay_iso_btns', {}).items():
            btn.background_color = (1.0, 0.48, 0.0, 1) if k == key else (0.15, 0.18, 0.22, 1)
        self.calc_decay()

    def calc_decay(self, *args):
        try:
            a0 = float(self.txt_decay_a0.text)
            days = float(self.txt_decay_days.text)
            if a0 <= 0 or days < 0:
                raise ValueError()

            hl = ISOTOPES[self.current_isotope]["half_life_days"]
            # A(t) = A0 * (0.5 ** (t / T_half))
            at = a0 * (0.5 ** (days / hl))
            remain_pct = (at / a0) * 100.0

            self.lbl_decay_val.text = fa(f"{at:.2f} Ci")
            self.lbl_decay_sub.text = fa(f"باقی‌مانده: {remain_pct:.1f}% | نیمه‌عمر: {hl:.1f} روز")

            # جدول ۷ روز آینده
            lines = []
            for d in range(1, 8):
                future_a = a0 * (0.5 ** ((days + d) / hl))
                lines.append(f"+{d} روز دیگر: {future_a:.2f} Ci")
            self.lbl_forecast_text.text = "\n".join(lines)
        except Exception:
            self.lbl_decay_val.text = fa("خطا")
            self.lbl_decay_sub.text = fa("ورودی نامعتبر")
            self.lbl_forecast_text.text = ""

    # ========================== تب ۳: زمان پرتودهی فیلم ==========================
    def build_exposure_tab(self):
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        box = BoxLayout(orientation='vertical', size_hint_y=None, padding=[16, 12, 16, 20], spacing=12)
        box.bind(minimum_height=box.setter('height'))

        # ورودی‌ها
        r1 = BoxLayout(spacing=10, size_hint_y=None, height=96)
        c1 = RoundedCard(orientation='vertical', padding=[8, 6], spacing=4)
        c1.add_widget(Label(text=fa("اکتیویته امروز (Ci)"), font_name=FONT_PATH, font_size='13sp', color=(0.8, 0.85, 0.9, 1)))
        self.txt_exp_act = TextInput(text="40", multiline=False, input_filter='float', font_size='18sp', halign='center',
                                     background_color=(0.14, 0.17, 0.20, 1), foreground_color=(1, 1, 1, 1))
        self.txt_exp_act.bind(text=self.calc_exposure)
        c1.add_widget(self.txt_exp_act)

        c2 = RoundedCard(orientation='vertical', padding=[8, 6], spacing=4)
        c2.add_widget(Label(text=fa("ضخامت فولاد (mm)"), font_name=FONT_PATH, font_size='13sp', color=(0.8, 0.85, 0.9, 1)))
        self.txt_exp_thick = TextInput(text="15", multiline=False, input_filter='float', font_size='18sp', halign='center',
                                       background_color=(0.14, 0.17, 0.20, 1), foreground_color=(1, 1, 1, 1))
        self.txt_exp_thick.bind(text=self.calc_exposure)
        c2.add_widget(self.txt_exp_thick)
        r1.add_widget(c1)
        r1.add_widget(c2)
        box.add_widget(r1)

        r2 = BoxLayout(spacing=10, size_hint_y=None, height=96)
        c3 = RoundedCard(orientation='vertical', padding=[8, 6], spacing=4)
        c3.add_widget(Label(text=fa("فاصله تا فیلم SFD (cm)"), font_name=FONT_PATH, font_size='13sp', color=(0.8, 0.85, 0.9, 1)))
        self.txt_exp_sfd = TextInput(text="50", multiline=False, input_filter='float', font_size='18sp', halign='center',
                                     background_color=(0.14, 0.17, 0.20, 1), foreground_color=(1, 1, 1, 1))
        self.txt_exp_sfd.bind(text=self.calc_exposure)
        c3.add_widget(self.txt_exp_sfd)

        c4 = RoundedCard(orientation='vertical', padding=[8, 6], spacing=4)
        c4.add_widget(Label(text=fa("فاکتور فیلم (D4=3 , D7=1)"), font_name=FONT_PATH, font_size='13sp', color=(0.8, 0.85, 0.9, 1)))
        self.txt_exp_ff = TextInput(text="1.2", multiline=False, input_filter='float', font_size='18sp', halign='center',
                                    background_color=(0.14, 0.17, 0.20, 1), foreground_color=(1, 1, 1, 1))
        self.txt_exp_ff.bind(text=self.calc_exposure)
        c4.add_widget(self.txt_exp_ff)
        r2.add_widget(c3)
        r2.add_widget(c4)
        box.add_widget(r2)

        # کارت نتیجه اکسپوژر
        c_res = RoundedCard(orientation='vertical', bg_color=(0.18, 0.12, 0.04, 0.95), border_color=(1.0, 0.65, 0.1, 1),
                            size_hint_y=None, height=136, padding=[12, 10], spacing=4)
        c_res.add_widget(Label(text=fa("زمان پرتودهی محاسبه‌شده (Exposure Time)"), font_name=FONT_PATH, font_size='14sp', color=(1, 0.85, 0.6, 1)))
        self.lbl_exp_val = Label(text="---", font_name=FONT_PATH, font_size='34sp', bold=True, color=(1, 0.72, 0.15, 1))
        self.lbl_exp_sub = Label(text="", font_name=FONT_PATH, font_size='13sp', color=(0.9, 0.8, 0.7, 1))
        c_res.add_widget(self.lbl_exp_val)
        c_res.add_widget(self.lbl_exp_sub)
        box.add_widget(c_res)

        scroll.add_widget(box)
        self.calc_exposure()
        return scroll

    def calc_exposure(self, *args):
        try:
            A = float(self.txt_exp_act.text)
            thick = float(self.txt_exp_thick.text)
            sfd_cm = float(self.txt_exp_sfd.text)
            ff = float(self.txt_exp_ff.text)
            if A <= 0 or sfd_cm <= 0 or ff <= 0:
                raise ValueError()

            iso = ISOTOPES[self.current_isotope]
            hvl_fe = iso["hvl_steel_mm"]

            # فرمول استاندارد اکسپوژر بر اساس تضعیف در فولاد و عکس مجذور SFD
            # Exposure = FF * 2^(Thickness / HVL_steel) * (SFD / 100)^2 / Activity
            # تبدیل به دقیقه
            sfd_m = sfd_cm / 100.0
            t_min = (ff * (2 ** (thick / hvl_fe)) * (sfd_m ** 2) * 6.0) / A

            mins = int(t_min)
            secs = int((t_min - mins) * 60)

            self.lbl_exp_val.text = fa(f"{mins} دقیقه و {secs} ثانیه")
            self.lbl_exp_sub.text = fa(f"ایزوتوپ: {iso['name']} | HVL فولاد: {hvl_fe}mm")
        except Exception:
            self.lbl_exp_val.text = fa("خطا در ورودی")
            self.lbl_exp_sub.text = fa("لطفاً مقادیر را صحیح وارد کنید")

    # ========================== تب ۴: جدول مشخصات و تماس ==========================
    def build_specs_tab(self):
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        box = BoxLayout(orientation='vertical', size_hint_y=None, padding=[16, 12, 16, 20], spacing=12)
        box.bind(minimum_height=box.setter('height'))

        # شناسنامه ایزوتوپ‌ها
        for k, v in ISOTOPES.items():
            card = RoundedCard(orientation='vertical', size_hint_y=None, height=120, padding=[12, 10], spacing=4)
            card.add_widget(Label(text=fa(f"ایزوتوپ {v['name']} ({v['fa_name']})"), font_name=FONT_PATH, font_size='15sp', bold=True, color=(1, 0.6, 0.1, 1)))
            card.add_widget(Label(text=f"Gamma Constant: {v['gamma']} R.m2/hr.Ci | Half-Life: {v['half_life_days']} days", font_size='12sp', color=(0.85, 0.85, 0.9, 1)))
            card.add_widget(Label(text=f"HVL Lead: {v['hvl_lead_mm']} mm | HVL Steel: {v['hvl_steel_mm']} mm", font_size='12sp', color=(0.7, 0.85, 0.8, 1)))
            card.add_widget(Label(text=f"Energy: {v['energy_range']}", font_size='11sp', color=(0.6, 0.75, 0.85, 1)))
            box.add_widget(card)

        # تماس با شرکت
        contact_card = RoundedCard(orientation='vertical', bg_color=(0.10, 0.12, 0.15, 1), border_color=(1, 0.48, 0, 1),
                                   size_hint_y=None, height=160, padding=[14, 12], spacing=6)
        contact_card.add_widget(Label(text=fa("شرکت رادیوگرافی صنعتی ایران"), font_name=FONT_PATH, font_size='16sp', bold=True, color=(1, 0.65, 0.1, 1)))
        contact_card.add_widget(Label(text=fa("ارائه‌دهنده تخصصی خدمات آزمون‌های غیرمخرب (NDT)"), font_name=FONT_PATH, font_size='12sp', color=(0.8, 0.85, 0.9, 1)))
        for p in COMPANY_PHONES:
            contact_card.add_widget(Label(text=f"📞  {p}", font_size='15sp', bold=True, color=(0.2, 0.9, 0.5, 1)))
        box.add_widget(contact_card)

        scroll.add_widget(box)
        return scroll


if __name__ == '__main__':
    NDTApp().run()
