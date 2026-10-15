# -*- coding: utf-8 -*-
import math
import os
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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_asset_path(filename):
    """یافتن فایل در اندروید و سیستم‌های مختلف"""
    candidates = [
        filename,
        os.path.join(BASE_DIR, filename),
        os.path.join(os.getcwd(), filename),
        os.path.abspath(filename),
        os.path.join(BASE_DIR, "..", filename)
    ]
    for p in candidates:
        if os.path.isfile(p):
            return p
    return None

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    def fa(text):
        if not text:
            return ""
        return get_display(arabic_reshaper.reshape(text))
except ImportError:
    def fa(text):
        return text

# پشتیبانی از نام‌های مختلف فونت
font_file = get_asset_path("Vazirmatn-Regular.ttf") or get_asset_path("font.ttf")
FONT_PATH = font_file if font_file else "Roboto"

ISOTOPES = {
    "Ir-192": {"name": "Ir-192", "fa": "ایریدیوم ۱۹۲", "gamma": 0.48, "hl": 73.83, "pb": 5.0, "fe": 13.0, "base_factor": 1.4},
    "Se-75":  {"name": "Se-75",  "fa": "سلنیوم ۷۵",  "gamma": 0.20, "hl": 119.8, "pb": 2.5, "fe": 8.0,  "base_factor": 2.2},
    "Co-60":  {"name": "Co-60",  "fa": "کبالت ۶۰",   "gamma": 1.32, "hl": 1925.0,"pb": 12.5,"fe": 22.0, "base_factor": 0.6},
    "Cs-137": {"name": "Cs-137", "fa": "سزیوم ۱۳۷",  "gamma": 0.33, "hl": 11000.0,"pb": 6.5,"fe": 16.0, "base_factor": 1.9}
}


class ModernCard(BoxLayout):
    def __init__(self, bg=(0.10, 0.12, 0.15, 0.92), border=(0.20, 0.24, 0.30, 0.9), radius=16, border_width=1.2, **kwargs):
        super(ModernCard, self).__init__(**kwargs)
        self.bg_color = bg
        self.border_color = border
        self.radius_val = radius
        self.border_width = border_width
        with self.canvas.before:
            self.c_bg = Color(*self.bg_color)
            self.r_bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(self.radius_val)])
            self.c_border = Color(*self.border_color)
            self.l_border = Line(rounded_rectangle=[self.x, self.y, self.width, self.height, dp(self.radius_val)], width=dp(self.border_width))
        self.bind(pos=self._redraw, size=self._redraw)

    def _redraw(self, *args):
        self.r_bg.pos = self.pos
        self.r_bg.size = self.size
        self.l_border.rounded_rectangle = [self.x, self.y, self.width, self.height, dp(self.radius_val)]


class StyledInput(TextInput):
    def __init__(self, **kwargs):
        super(StyledInput, self).__init__(**kwargs)
        self.multiline = False
        self.input_filter = 'float'
        self.font_size = sp(18)
        self.font_name = FONT_PATH
        self.halign = 'center'
        self.background_normal = ''
        self.background_active = ''
        self.background_color = (0.05, 0.06, 0.08, 0.95)
        self.foreground_color = (1, 1, 1, 1)
        self.cursor_color = (1, 0.48, 0, 1)
        self.padding = [dp(10), dp(10)]
        with self.canvas.after:
            Color(0.24, 0.28, 0.35, 1)
            self.border_line = Line(rounded_rectangle=[self.x, self.y, self.width, self.height, dp(10)], width=dp(1.2))
        self.bind(pos=self._update_border, size=self._update_border)

    def _update_border(self, *args):
        self.border_line.rounded_rectangle = [self.x, self.y, self.width, self.height, dp(10)]


class NDTApp(App):
    def build(self):
        Window.clearcolor = (0.05, 0.06, 0.07, 1)
        self.current_iso = "Ir-192"

        # FloatLayout برای لایه‌بندی پس‌زمینه
        main_root = FloatLayout()

        # ----------------- پس‌زمینه (bg.png) -----------------
        bg_file = get_asset_path("bg.png")
        if bg_file:
            bg_image = Image(
                source=bg_file,
                allow_stretch=True,
                keep_ratio=False,
                size_hint=(1, 1),
                pos_hint={'x': 0, 'y': 0}
            )
            main_root.add_widget(bg_image)

            overlay = BoxLayout(size_hint=(1, 1))
            with overlay.canvas.before:
                Color(0.04, 0.05, 0.07, 0.85)
                self.rect_overlay = Rectangle(pos=overlay.pos, size=overlay.size)
            overlay.bind(pos=lambda inst, val: setattr(self.rect_overlay, 'pos', val),
                         size=lambda inst, val: setattr(self.rect_overlay, 'size', val))
            main_root.add_widget(overlay)

        # ----------------- بدنه اصلی برنامه -----------------
        root = BoxLayout(orientation='vertical', size_hint=(1, 1))

        # نوار هدر (لوگو + عنوان شرکت)
        header = ModernCard(
            orientation='horizontal',
            bg=(0.08, 0.09, 0.11, 0.98),
            border=(1.0, 0.48, 0.0, 0.5),
            radius=0,
            border_width=1,
            size_hint_y=None,
            height=dp(70),
            padding=[dp(12), dp(8), dp(16), dp(8)],
            spacing=dp(12)
        )

        logo_path = get_asset_path("logo.png") or get_asset_path("icon.png")
        if logo_path:
            logo_img = Image(
                source=logo_path,
                size_hint=(None, None),
                size=(dp(54), dp(54)),
                allow_stretch=True,
                keep_ratio=True
            )
            header.add_widget(logo_img)
        else:
            fallback_lbl = Label(
                text="☢",
                font_size=sp(30),
                size_hint=(None, 1),
                width=dp(40),
                color=(1, 0.55, 0.05, 1)
            )
            header.add_widget(fallback_lbl)

        h_title = Label(
            text=fa("شرکت رادیوگرافی صنعتی ایران"),
            font_name=FONT_PATH,
            font_size=sp(16),
            bold=True,
            color=(1, 0.55, 0.05, 1),
            halign='right',
            valign='middle'
        )
        h_title.bind(size=h_title.setter('text_size'))
        header.add_widget(h_title)
        root.add_widget(header)

        self.container = BoxLayout(size_hint=(1, 1))
        root.add_widget(self.container)

        # نوار دکمه‌های پایین
        nav = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(62),
            padding=[dp(6), dp(6), dp(6), dp(6)],
            spacing=dp(6)
        )
        with nav.canvas.before:
            Color(0.07, 0.08, 0.10, 0.98)
            RoundedRectangle(pos=nav.pos, size=nav.size)

        self.tab_buttons = {}
        tabs = [
            ("distance", fa("مرزبندی و حفاظ")),
            ("decay", fa("واپاشی روز")),
            ("exposure", fa("زمان پرتودهی")),
            ("specs", fa("شناسنامه ایزوتوپ"))
        ]

        for tid, label in tabs:
            btn = Button(
                text=label,
                font_name=FONT_PATH,
                font_size=sp(12),
                bold=True,
                background_normal='',
                background_color=(0.13, 0.15, 0.18, 1),
                color=(0.8, 0.85, 0.9, 1)
            )
            btn.bind(on_release=lambda inst, t=tid: self.switch_view(t))
            self.tab_buttons[tid] = btn
            nav.add_widget(btn)

        root.add_widget(nav)
        main_root.add_widget(root)

        self.switch_view("exposure")
        return main_root

    def switch_view(self, tab_id):
        for tid, btn in self.tab_buttons.items():
            if tid == tab_id:
                btn.background_color = (1.0, 0.48, 0.0, 1)
                btn.color = (0.05, 0.05, 0.05, 1)
            else:
                btn.background_color = (0.13, 0.15, 0.18, 1)
                btn.color = (0.75, 0.80, 0.85, 1)

        self.container.clear_widgets()
        if tab_id == "distance":
            self.container.add_widget(self.render_distance_screen())
        elif tab_id == "decay":
            self.container.add_widget(self.render_decay_screen())
        elif tab_id == "exposure":
            self.container.add_widget(self.render_exposure_screen())
        elif tab_id == "specs":
            self.container.add_widget(self.render_specs_screen())

    # ----------------- ۱. زمان پرتودهی -----------------
    def render_exposure_screen(self):
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        box = BoxLayout(orientation='vertical', size_hint_y=None, padding=dp(16), spacing=dp(12))
        box.bind(minimum_height=box.setter('height'))

        c_iso = ModernCard(orientation='vertical', size_hint_y=None, height=dp(88), padding=dp(8), spacing=dp(6))
        c_iso.add_widget(Label(text=fa("ایزوتوپ پرتودهی"), font_name=FONT_PATH, font_size=sp(12), color=(0.8, 0.85, 0.9, 1)))
        grid = GridLayout(cols=4, spacing=dp(6), size_hint_y=None, height=dp(38))
        self.exp_iso_btns = {}
        for k in ["Ir-192", "Se-75", "Co-60", "Cs-137"]:
            b = Button(
                text=k,
                font_size=sp(13),
                bold=True,
                background_normal='',
                background_color=(1.0, 0.48, 0.0, 1) if k == self.current_iso else (0.16, 0.19, 0.23, 1),
                color=(1, 1, 1, 1)
            )
            b.bind(on_release=lambda inst, key=k: self.select_exp_iso(key))
            self.exp_iso_btns[k] = b
            grid.add_widget(b)
        c_iso.add_widget(grid)
        box.add_widget(c_iso)

        r1 = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(100))
        c_act = ModernCard(orientation='vertical', padding=dp(8), spacing=dp(4))
        c_act.add_widget(Label(text=fa("اکتیویته (Ci)"), font_name=FONT_PATH, font_size=sp(12), color=(0.8, 0.85, 0.9, 1)))
        self.in_exp_a = StyledInput(text="40")
        self.in_exp_a.bind(text=self.recalculate_exposure)
        c_act.add_widget(self.in_exp_a)

        c_th = ModernCard(orientation='vertical', padding=dp(8), spacing=dp(4))
        c_th.add_widget(Label(text=fa("ضخامت فولاد (mm)"), font_name=FONT_PATH, font_size=sp(12), color=(0.8, 0.85, 0.9, 1)))
        self.in_exp_th = StyledInput(text="23")
        self.in_exp_th.bind(text=self.recalculate_exposure)
        c_th.add_widget(self.in_exp_th)
        r1.add_widget(c_act)
        r1.add_widget(c_th)
        box.add_widget(r1)

        r2 = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(100))
        c_sfd = ModernCard(orientation='vertical', padding=dp(8), spacing=dp(4))
        c_sfd.add_widget(Label(text=fa("فاصله SFD (cm)"), font_name=FONT_PATH, font_size=sp(12), color=(0.8, 0.85, 0.9, 1)))
        self.in_exp_sfd = StyledInput(text="50")
        self.in_exp_sfd.bind(text=self.recalculate_exposure)
        c_sfd.add_widget(self.in_exp_sfd)

        c_ff = ModernCard(orientation='vertical', padding=dp(8), spacing=dp(4))
        c_ff.add_widget(Label(text=fa("فاکتور فیلم (D7=1 , D4=3)"), font_name=FONT_PATH, font_size=sp(12), color=(0.8, 0.85, 0.9, 1)))
        self.in_exp_ff = StyledInput(text="1.0")
        self.in_exp_ff.bind(text=self.recalculate_exposure)
        c_ff.add_widget(self.in_exp_ff)
        r2.add_widget(c_sfd)
        r2.add_widget(c_ff)
        box.add_widget(r2)

        self.c_exp_res = ModernCard(
            orientation='vertical',
            bg=(0.20, 0.12, 0.04, 0.95),
            border=(1.0, 0.65, 0.1, 1),
            radius=18,
            size_hint_y=None,
            height=dp(140),
            padding=dp(12),
            spacing=dp(4)
        )
        self.c_exp_res.add_widget(Label(text=fa("زمان پرتودهی محاسبه‌شده (Exposure Time)"), font_name=FONT_PATH, font_size=sp(13), color=(1, 0.85, 0.6, 1)))
        self.lbl_exp_val = Label(text="---", font_name=FONT_PATH, font_size=sp(28), bold=True, color=(1, 0.72, 0.15, 1))
        self.lbl_exp_sub = Label(text="", font_name=FONT_PATH, font_size=sp(11), color=(0.9, 0.8, 0.7, 1))
        self.c_exp_res.add_widget(self.lbl_exp_val)
        self.c_exp_res.add_widget(self.lbl_exp_sub)
        box.add_widget(self.c_exp_res)

        scroll.add_widget(box)
        self.recalculate_exposure()
        return scroll

    def select_exp_iso(self, key):
        self.current_iso = key
        for k, btn in getattr(self, 'exp_iso_btns', {}).items():
            btn.background_color = (1.0, 0.48, 0.0, 1) if k == key else (0.16, 0.19, 0.23, 1)
        self.recalculate_exposure()

    def recalculate_exposure(self, *args):
        try:
            txt_a = self.in_exp_a.text.strip()
            txt_th = self.in_exp_th.text.strip()
            txt_sfd = self.in_exp_sfd.text.strip()
            txt_ff = self.in_exp_ff.text.strip()

            if not txt_a or not txt_th or not txt_sfd:
                self.lbl_exp_val.text = fa("در انتظار ورودی...")
                self.lbl_exp_sub.text = fa("لطفاً مقادیر را تکمیل نمایید")
                return

            A = float(txt_a)
            th = float(txt_th)
            sfd_cm = float(txt_sfd)
            ff = float(txt_ff) if txt_ff else 1.0

            if A <= 0 or sfd_cm <= 0 or ff <= 0 or th < 0:
                raise ValueError()

            iso = ISOTOPES[self.current_iso]
            hvl_fe = iso["fe"]
            base_factor = iso.get("base_factor", 1.4)

            sfd_ratio = (sfd_cm / 50.0) ** 2
            half_value_layers = th / hvl_fe
            attenuation = 2.0 ** half_value_layers
            
            t_total_seconds = (base_factor * ff * attenuation * sfd_ratio * 120.0) / (A / 10.0)
            
            mins = int(t_total_seconds // 60)
            secs = int(t_total_seconds % 60)

            if mins > 0:
                self.lbl_exp_val.text = fa(f"{mins} دقیقه و {secs} ثانیه")
            else:
                self.lbl_exp_val.text = fa(f"{secs} ثانیه")

            self.lbl_exp_sub.text = fa(f"ایزوتوپ: {self.current_iso} | تعداد HVL: {half_value_layers:.1f} | SFD: {sfd_cm:.0f}cm")
        except Exception:
            self.lbl_exp_val.text = fa("خطا در ورودی")
            self.lbl_exp_sub.text = fa("لطفاً فقط اعداد مجاز وارد کنید")

    # ----------------- ۲. مرزبندی و ایمنی -----------------
    def render_distance_screen(self):
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        box = BoxLayout(orientation='vertical', size_hint_y=None, padding=dp(16), spacing=dp(12))
        box.bind(minimum_height=box.setter('height'))

        c_iso = ModernCard(orientation='vertical', size_hint_y=None, height=dp(94), padding=dp(8), spacing=dp(6))
        c_iso.add_widget(Label(text=fa("انتخاب ایزوتوپ"), font_name=FONT_PATH, font_size=sp(12), color=(0.8, 0.85, 0.9, 1)))
        grid = GridLayout(cols=4, spacing=dp(6), size_hint_y=None, height=dp(40))
        self.dist_btns = {}
        for k in ["Ir-192", "Se-75", "Co-60", "Cs-137"]:
            b = Button(
                text=k,
                font_size=sp(13),
                bold=True,
                background_normal='',
                background_color=(1.0, 0.48, 0.0, 1) if k == self.current_iso else (0.16, 0.19, 0.23, 1),
                color=(1, 1, 1, 1)
            )
            b.bind(on_release=lambda inst, key=k: self.select_dist_iso(key))
            self.dist_btns[k] = b
            grid.add_widget(b)
        c_iso.add_widget(grid)
        box.add_widget(c_iso)

        r1 = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(100))
        c_act = ModernCard(orientation='vertical', padding=dp(8), spacing=dp(4))
        c_act.add_widget(Label(text=fa("اکتیویته (Ci)"), font_name=FONT_PATH, font_size=sp(12), color=(0.8, 0.85, 0.9, 1)))
        self.in_act = StyledInput(text="40")
        self.in_act.bind(text=self.recalculate_distance)
        c_act.add_widget(self.in_act)

        c_dose = ModernCard(orientation='vertical', padding=dp(8), spacing=dp(4))
        c_dose.add_widget(Label(text=fa("حد دوز (µSv/h)"), font_name=FONT_PATH, font_size=sp(12), color=(0.8, 0.85, 0.9, 1)))
        self.in_dose = StyledInput(text="7.5")
        self.in_dose.bind(text=self.recalculate_distance)
        c_dose.add_widget(self.in_dose)
        r1.add_widget(c_act)
        r1.add_widget(c_dose)
        box.add_widget(r1)

        c_sh = ModernCard(orientation='vertical', size_hint_y=None, height=dp(94), padding=dp(8), spacing=dp(4))
        c_sh.add_widget(Label(text=fa("ضخامت حفاظ سربی یا کلیماتور (mm)"), font_name=FONT_PATH, font_size=sp(12), color=(0.8, 0.85, 0.9, 1)))
        self.in_lead = StyledInput(text="0")
        self.in_lead.bind(text=self.recalculate_distance)
        c_sh.add_widget(self.in_lead)
        box.add_widget(c_sh)

        self.dist_res = ModernCard(
            orientation='vertical',
            bg=(0.04, 0.17, 0.11, 0.95),
            border=(0.15, 0.95, 0.50, 1),
            radius=18,
            size_hint_y=None,
            height=dp(150),
            padding=dp(10),
            spacing=dp(3)
        )
        self.lbl_dist_title = Label(text=fa("شعاع فاصله طناب‌کشی ایمن"), font_name=FONT_PATH, font_size=sp(13), color=(0.8, 0.98, 0.85, 1))
        self.lbl_dist_val = Label(text="---", font_name=FONT_PATH, font_size=sp(32), bold=True, color=(0.2, 0.98, 0.55, 1))
        self.lbl_dist_sub = Label(text="", font_name=FONT_PATH, font_size=sp(11), color=(0.7, 0.85, 0.8, 1))
        self.lbl_operator_pos = Label(text="", font_name=FONT_PATH, font_size=sp(11), bold=True, color=(1, 0.85, 0.4, 1))
        self.dist_res.add_widget(self.lbl_dist_title)
        self.dist_res.add_widget(self.lbl_dist_val)
        self.dist_res.add_widget(self.lbl_dist_sub)
        self.dist_res.add_widget(self.lbl_operator_pos)
        box.add_widget(self.dist_res)

        scroll.add_widget(box)
        self.recalculate_distance()
        return scroll

    def select_dist_iso(self, key):
        self.current_iso = key
        for k, btn in getattr(self, 'dist_btns', {}).items():
            btn.background_color = (1.0, 0.48, 0.0, 1) if k == key else (0.16, 0.19, 0.23, 1)
        self.recalculate_distance()

    def recalculate_distance(self, *args):
        try:
            A = float(self.in_act.text)
            dose_uSv = float(self.in_dose.text)
            lead_mm = float(self.in_lead.text) if self.in_lead.text else 0.0
            if A <= 0 or dose_uSv <= 0:
                raise ValueError()

            iso = ISOTOPES[self.current_iso]
            gamma = iso["gamma"]
            hvl = iso["pb"]

            attenuation = 0.5 ** (lead_mm / hvl) if lead_mm > 0 else 1.0
            eff_a = A * attenuation
            dose_r_hr = dose_uSv / 10000.0
            d = math.sqrt((gamma * eff_a) / dose_r_hr)

            self.lbl_dist_val.text = fa(f"{d:.1f} متر")
            self.lbl_dist_sub.text = fa(f"ایزوتوپ: {iso['name']} | تضعیف حفاظ: {attenuation:.2f}")
            op_d = d * 1.25
            self.lbl_operator_pos.text = fa(f"👤 استقرار مجاز اپراتور: حداقل {op_d:.1f} متری چشمه")
        except Exception:
            self.lbl_dist_val.text = fa("خطا در ورودی")
            self.lbl_dist_sub.text = fa("مقادیر معتبر وارد نمایید")
            self.lbl_operator_pos.text = fa("")

    # ----------------- ۳. واپاشی روزانه -----------------
    def render_decay_screen(self):
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        box = BoxLayout(orientation='vertical', size_hint_y=None, padding=dp(16), spacing=dp(12))
        box.bind(minimum_height=box.setter('height'))

        row = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(100))
        c1 = ModernCard(orientation='vertical', padding=dp(8), spacing=dp(4))
        c1.add_widget(Label(text=fa("اکتیویته اولیه (Ci)"), font_name=FONT_PATH, font_size=sp(12), color=(0.8, 0.85, 0.9, 1)))
        self.in_decay_a0 = StyledInput(text="80")
        self.in_decay_a0.bind(text=self.recalculate_decay)
        c1.add_widget(self.in_decay_a0)

        c2 = ModernCard(orientation='vertical', padding=dp(8), spacing=dp(4))
        c2.add_widget(Label(text=fa("روزهای گذشته"), font_name=FONT_PATH, font_size=sp(12), color=(0.8, 0.85, 0.9, 1)))
        self.in_decay_days = StyledInput(text="45")
        self.in_decay_days.bind(text=self.recalculate_decay)
        c2.add_widget(self.in_decay_days)

        row.add_widget(c1)
        row.add_widget(c2)
        box.add_widget(row)

        c_res = ModernCard(
            orientation='vertical',
            bg=(0.05, 0.16, 0.24, 0.95),
            border=(0.2, 0.65, 0.95, 1),
            radius=18,
            size_hint_y=None,
            height=dp(130),
            padding=dp(10),
            spacing=dp(3)
        )
        c_res.add_widget(Label(text=fa("اکتیویته دقیق روز جاری"), font_name=FONT_PATH, font_size=sp(13), color=(0.75, 0.9, 1, 1)))
        self.lbl_decay_val = Label(text="---", font_name=FONT_PATH, font_size=sp(32), bold=True, color=(0.3, 0.8, 1, 1))
        self.lbl_decay_sub = Label(text="", font_name=FONT_PATH, font_size=sp(11), color=(0.7, 0.85, 0.9, 1))
        c_res.add_widget(self.lbl_decay_val)
        c_res.add_widget(self.lbl_decay_sub)
        box.add_widget(c_res)

        c_plaque = ModernCard(orientation='vertical', size_hint_y=None, height=dp(200), padding=dp(10), spacing=dp(3))
        c_plaque.add_widget(Label(text=fa("جدول پلاک روزانه (۷ روز آینده)"), font_name=FONT_PATH, font_size=sp(12), bold=True, color=(1, 0.7, 0.2, 1)))
        self.lbl_plaque = Label(text="", font_name=FONT_PATH, font_size=sp(11), color=(0.85, 0.85, 0.85, 1))
        c_plaque.add_widget(self.lbl_plaque)
        box.add_widget(c_plaque)

        scroll.add_widget(box)
        self.recalculate_decay()
        return scroll

    def recalculate_decay(self, *args):
        try:
            a0 = float(self.in_decay_a0.text)
            days = float(self.in_decay_days.text)
            if a0 <= 0 or days < 0:
                raise ValueError()

            hl = ISOTOPES[self.current_iso]["hl"]
            at = a0 * (0.5 ** (days / hl))
            pct = (at / a0) * 100.0

            self.lbl_decay_val.text = fa(f"{at:.2f} Ci")
            self.lbl_decay_sub.text = fa(f"باقی‌مانده: {pct:.1f}% | نیمه‌عمر: {hl:.1f} روز")

            lines = []
            for d in range(1, 8):
                nxt = a0 * (0.5 ** ((days + d) / hl))
                lines.append(f"+{d} روز بعد:  {nxt:.2f} Ci")
            self.lbl_plaque.text = "\n".join(lines)
        except Exception:
            self.lbl_decay_val.text = fa("خطا")
            self.lbl_decay_sub.text = fa("ورودی نامعتبر")
            self.lbl_plaque.text = ""

    # ----------------- ۴. شناسنامه و اطلاعات شرکت -----------------
    def render_specs_screen(self):
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        box = BoxLayout(orientation='vertical', size_hint_y=None, padding=dp(16), spacing=dp(12))
        box.bind(minimum_height=box.setter('height'))

        banner_path = get_asset_path("company_banner.png")
        if banner_path:
            c_banner = ModernCard(size_hint_y=None, height=dp(120), padding=dp(4))
            c_banner.add_widget(Image(source=banner_path, allow_stretch=True, keep_ratio=True))
            box.add_widget(c_banner)

        for k, v in ISOTOPES.items():
            card = ModernCard(orientation='vertical', size_hint_y=None, height=dp(100), padding=dp(8), spacing=dp(3))
            card.add_widget(Label(text=fa(f"ایزوتوپ {v['name']} ({v['fa']})"), font_name=FONT_PATH, font_size=sp(13), bold=True, color=(1, 0.6, 0.1, 1)))
            card.add_widget(Label(text=f"Gamma Constant: {v['gamma']} R.m2/hr.Ci | Half-Life: {v['hl']} days", font_size=sp(11), color=(0.85, 0.85, 0.9, 1)))
            card.add_widget(Label(text=f"HVL Lead: {v['pb']} mm | HVL Steel: {v['fe']} mm", font_size=sp(11), color=(0.7, 0.85, 0.8, 1)))
            box.add_widget(card)

        contact = ModernCard(
            orientation='vertical',
            bg=(0.10, 0.12, 0.16, 0.95),
            border=(1, 0.48, 0, 1),
            size_hint_y=None,
            height=dp(140),
            padding=dp(10),
            spacing=dp(3)
        )
        contact.add_widget(Label(text=fa("شرکت رادیوگرافی صنعتی ایران"), font_name=FONT_PATH, font_size=sp(14), bold=True, color=(1, 0.65, 0.1, 1)))
        for p in ["09122012248", "09121042253", "09121326011"]:
            contact.add_widget(Label(text=f"📞  {p}", font_size=sp(13), bold=True, color=(0.2, 0.9, 0.5, 1)))
        box.add_widget(contact)

        scroll.add_widget(box)
        return scroll


if __name__ == '__main__':
    NDTApp().run()
