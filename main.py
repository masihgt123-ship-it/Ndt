# -*- coding: utf-8 -*-
import os
import math
from datetime import datetime

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
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.graphics import Color, RoundedRectangle, Rectangle

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
    'Ir-192': {'gamma': 0.48, 'hvl_pb': 4.8, 'hvl_fe': 12.5, 'half_life': 73.83, 'name': 'ایریدیوم ۱۹۲', 'energy': '0.38 MeV'},
    'Se-75':  {'gamma': 0.20, 'hvl_pb': 2.0, 'hvl_fe': 8.0,  'half_life': 119.78, 'name': 'سلنیوم ۷۵', 'energy': '0.32 MeV'},
    'Co-60':  {'gamma': 1.32, 'hvl_pb': 12.5,'hvl_fe': 21.0, 'half_life': 1925.0, 'name': 'کبالت ۶۰', 'energy': '1.25 MeV'},
    'Cs-137': {'gamma': 0.33, 'hvl_pb': 6.5, 'hvl_fe': 16.0, 'half_life': 11000.0, 'name': 'سزیوم ۱۳۷', 'energy': '0.66 MeV'}
}

class SafeCard(BoxLayout):
    def __init__(self, bg_color=(0.10, 0.12, 0.15, 0.95), border_color=None, radius=10, **kwargs):
        super(SafeCard, self).__init__(**kwargs)
        self.bg_color = bg_color
        self.border_color = border_color
        self.radius = radius
        with self.canvas.before:
            if self.border_color:
                Color(*self.border_color)
                self.border_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[radius+1])
            Color(*self.bg_color)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[radius])
        self.bind(pos=self._update_rect, size=self._update_rect)

    def _update_rect(self, *args):
        if hasattr(self, 'border_rect'):
            self.border_rect.pos = (self.pos[0]-1, self.pos[1]-1)
            self.border_rect.size = (self.size[0]+2, self.size[1]+2)
        self.rect.pos = self.pos
        self.rect.size = self.size

class SafeInput(TextInput):
    def __init__(self, **kwargs):
        super(SafeInput, self).__init__(**kwargs)
        self.background_normal = ''
        self.background_active = ''
        self.background_color = (0.05, 0.06, 0.08, 1.0)
        self.foreground_color = (1.0, 1.0, 1.0, 1.0)
        self.cursor_color = (1.0, 0.48, 0.0, 1.0)
        self.font_size = sp(16)
        self.bold = True
        self.multiline = False
        self.halign = 'center'
        self.padding = [dp(6), dp(10), dp(6), dp(10)]
        font_kw = {'font_name': FONT_PATH} if FONT_PATH and os.path.exists(FONT_PATH) else {}
        for k, v in font_kw.items():
            setattr(self, k, v)


# ----------------- صفحه ۱: مرزبندی و حفاظ (گاما) -----------------
class SafetyScreen(Screen):
    def __init__(self, app, **kwargs):
        super(SafetyScreen, self).__init__(**kwargs)
        self.app = app
        font_kw = {'font_name': FONT_PATH} if FONT_PATH and os.path.exists(FONT_PATH) else {}

        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        content = BoxLayout(orientation='vertical', size_hint_y=None, padding=[dp(12), dp(8)], spacing=dp(10))
        content.bind(minimum_height=content.setter('height'))

        # انتخاب ایزوتوپ
        iso_card = SafeCard(orientation='vertical', size_hint_y=None, height=dp(80), padding=dp(8), spacing=dp(6))
        iso_card.add_widget(Label(text=fa('انتخاب ایزوتوپ'), font_size=sp(12), color=(0.8, 0.85, 0.9, 1.0), size_hint_y=None, height=dp(20), **font_kw))
        
        grid_iso = GridLayout(cols=4, spacing=dp(6), size_hint_y=None, height=dp(38))
        self.iso_btns = {}
        for s in ['Ir-192', 'Se-75', 'Co-60', 'Cs-137']:
            b = Button(
                text=s, bold=True, font_size=sp(13),
                background_normal='',
                background_color=(1.0, 0.45, 0.0, 1.0) if s == self.app.current_source else (0.16, 0.18, 0.22, 1.0),
                color=(1, 1, 1, 1), **font_kw
            )
            b.bind(on_release=lambda inst, name=s: self.set_iso(name))
            self.iso_btns[s] = b
            grid_iso.add_widget(b)
        iso_card.add_widget(grid_iso)
        content.add_widget(iso_card)

        # ورودی‌های اکتیویته و دوز مجاز (دو ستونه)
        row1 = GridLayout(cols=2, spacing=dp(8), size_hint_y=None, height=dp(95))
        
        c_act = SafeCard(orientation='vertical', padding=dp(6), spacing=dp(4))
        c_act.add_widget(Label(text=fa('اکتیویته (Ci)'), font_size=sp(11), color=(0.75, 0.8, 0.85, 1.0), size_hint_y=None, height=dp(18), **font_kw))
        self.in_act = SafeInput(text='40')
        self.in_act.bind(text=self.calc)
        c_act.add_widget(self.in_act)
        row1.add_widget(c_act)

        c_dose = SafeCard(orientation='vertical', padding=dp(6), spacing=dp(4))
        c_dose.add_widget(Label(text=fa('حد دوز (µSv/h)'), font_size=sp(11), color=(0.75, 0.8, 0.85, 1.0), size_hint_y=None, height=dp(18), **font_kw))
        self.in_dose = SafeInput(text='2.5')
        self.in_dose.bind(text=self.calc)
        c_dose.add_widget(self.in_dose)
        row1.add_widget(c_dose)
        content.add_widget(row1)

        # ضخامت کولیماتور سرب
        c_sh = SafeCard(orientation='vertical', size_hint_y=None, height=dp(85), padding=dp(6), spacing=dp(4))
        c_sh.add_widget(Label(text=fa('ضخامت حفاظ سربی یا کولیماتور (mm)'), font_size=sp(11), color=(0.75, 0.8, 0.85, 1.0), size_hint_y=None, height=dp(18), **font_kw))
        self.in_sh = SafeInput(text='0')
        self.in_sh.bind(text=self.calc)
        c_sh.add_widget(self.in_sh)
        content.add_widget(c_sh)

        # کارت سبز نئونی نتیجه (دقیقاً مثل عکس ارسالی)
        self.res_card = SafeCard(
            orientation='vertical',
            bg_color=(0.04, 0.12, 0.08, 0.95),
            border_color=(0.10, 0.85, 0.40, 1.0),
            radius=12,
            size_hint_y=None,
            height=dp(165),
            padding=dp(10),
            spacing=dp(4)
        )
        self.res_card.add_widget(Label(text=fa('شعاع فاصله طناب‌کشی ایمن'), font_size=sp(12), color=(0.8, 0.9, 0.85, 1.0), size_hint_y=None, height=dp(20), **font_kw))
        self.lbl_dist = Label(text=fa('309.8 متر'), font_size=sp(28), bold=True, color=(0.15, 1.0, 0.45, 1.0), size_hint_y=None, height=dp(45), **font_kw)
        self.lbl_info = Label(text=fa('ایزوتوپ: Ir-192 | تضعیف حفاظ: 1.00'), font_size=sp(11), color=(0.7, 0.8, 0.75, 1.0), size_hint_y=None, height=dp(20), **font_kw)
        self.lbl_op = Label(text=fa('استقرار مجاز اپراتور: حداقل 387.3 متری چشمه'), font_size=sp(12), bold=True, color=(1.0, 0.82, 0.25, 1.0), size_hint_y=None, height=dp(25), **font_kw)

        self.res_card.add_widget(self.lbl_dist)
        self.res_card.add_widget(self.lbl_info)
        self.res_card.add_widget(self.lbl_op)
        content.add_widget(self.res_card)

        scroll.add_widget(content)
        self.add_widget(scroll)
        self.calc()

    def set_iso(self, name):
        self.app.current_source = name
        for s, b in self.iso_btns.items():
            b.background_color = (1.0, 0.45, 0.0, 1.0) if s == name else (0.16, 0.18, 0.22, 1.0)
        self.calc()

    def calc(self, *args):
        try:
            curie = float(self.in_act.text.strip() or '0')
            dose_lim = float(self.in_dose.text.strip() or '2.5')
            shield = float(self.in_sh.text.strip() or '0')
            dose_lim = max(0.1, dose_lim)

            iso = ISOTOPES.get(self.app.current_source, ISOTOPES['Ir-192'])
            trans = math.pow(2.0, -(shield / iso['hvl_pb'])) if iso['hvl_pb'] > 0 else 1.0
            dose_1m = iso['gamma'] * curie * 10000.0 * trans
            dist = math.sqrt(max(0.01, dose_1m) / dose_lim)
            op = dist * 1.25

            self.lbl_dist.text = fa(f"{dist:.1f} متر")
            self.lbl_info.text = fa(f"ایزوتوپ: {self.app.current_source} | تضعیف حفاظ: {trans:.2f}")
            self.lbl_op.text = fa(f"استقرار مجاز اپراتور: حداقل {op:.1f} متری چشمه")
        except Exception:
            pass


# ----------------- صفحه ۲: ایکس‌ری (X-Ray) -----------------
class XRayScreen(Screen):
    def __init__(self, app, **kwargs):
        super(XRayScreen, self).__init__(**kwargs)
        self.app = app
        font_kw = {'font_name': FONT_PATH} if FONT_PATH and os.path.exists(FONT_PATH) else {}

        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        content = BoxLayout(orientation='vertical', size_hint_y=None, padding=[dp(12), dp(8)], spacing=dp(10))
        content.bind(minimum_height=content.setter('height'))

        header = SafeCard(size_hint_y=None, height=dp(40), padding=dp(6))
        header.add_widget(Label(text=fa('محاسبات دستگاه مولد پرتو ایکس (X-Ray)'), bold=True, font_size=sp(13), color=(1.0, 0.5, 0.0, 1.0), **font_kw))
        content.add_widget(header)

        row = GridLayout(cols=2, spacing=dp(8), size_hint_y=None, height=dp(95))
        c_kv = SafeCard(orientation='vertical', padding=dp(6))
        c_kv.add_widget(Label(text=fa('ولتاژ تیوب (kV)'), font_size=sp(11), color=(0.8, 0.8, 0.8, 1.0), **font_kw))
        self.in_kv = SafeInput(text='200')
        self.in_kv.bind(text=self.calc)
        c_kv.add_widget(self.in_kv)
        row.add_widget(c_kv)

        c_ma = SafeCard(orientation='vertical', padding=dp(6))
        c_ma.add_widget(Label(text=fa('جریان تیوب (mA)'), font_size=sp(11), color=(0.8, 0.8, 0.8, 1.0), **font_kw))
        self.in_ma = SafeInput(text='4.0')
        self.in_ma.bind(text=self.calc)
        c_ma.add_widget(self.in_ma)
        row.add_widget(c_ma)
        content.add_widget(row)

        c_th = SafeCard(orientation='vertical', size_hint_y=None, height=dp(85), padding=dp(6))
        c_th.add_widget(Label(text=fa('ضخامت قطعه فولادی (mm)'), font_size=sp(11), color=(0.8, 0.8, 0.8, 1.0), **font_kw))
        self.in_th = SafeInput(text='12')
        self.in_th.bind(text=self.calc)
        c_th.add_widget(self.in_th)
        content.add_widget(c_th)

        self.res = SafeCard(orientation='vertical', bg_color=(0.04, 0.12, 0.08, 0.95), border_color=(0.10, 0.85, 0.40, 1.0), radius=12, size_hint_y=None, height=dp(140), padding=dp(10))
        self.res.add_widget(Label(text=fa('فاصله ایمن بدون حفاظ'), font_size=sp(12), color=(0.8, 0.9, 0.85, 1.0), **font_kw))
        self.lbl_xd = Label(text=fa('-- متر'), font_size=sp(26), bold=True, color=(0.15, 1.0, 0.45, 1.0), **font_kw)
        self.lbl_xi = Label(text=fa('خروجی تابش و زمان تخمینی'), font_size=sp(11), color=(0.7, 0.8, 0.75, 1.0), **font_kw)
        self.res.add_widget(self.lbl_xd)
        self.res.add_widget(self.lbl_xi)
        content.add_widget(self.res)

        scroll.add_widget(content)
        self.add_widget(scroll)
        self.calc()

    def calc(self, *args):
        try:
            kv = max(50.0, float(self.in_kv.text.strip() or '200'))
            ma = max(0.5, float(self.in_ma.text.strip() or '4'))
            th = max(0.0, float(self.in_th.text.strip() or '12'))
            out_rate = math.pow(kv / 100.0, 2.4) * 0.14 * ma * 60.0 * 10000.0
            dist = math.sqrt(out_rate / 7.5)
            hvl = 4.0 + (kv / 50.0)
            t_sec = (45.0 * math.pow(2.0, th / hvl)) / (ma * (kv / 150.0))
            self.lbl_xd.text = fa(f"{dist:.1f} متر")
            self.lbl_xi.text = fa(f"تخمین زمان اکسپوژر فولاد: {t_sec:.1f} ثانیه")
        except Exception:
            pass


# ----------------- صفحه ۳: واپاشی روز -----------------
class DecayScreen(Screen):
    def __init__(self, app, **kwargs):
        super(DecayScreen, self).__init__(**kwargs)
        self.app = app
        font_kw = {'font_name': FONT_PATH} if FONT_PATH and os.path.exists(FONT_PATH) else {}

        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        content = BoxLayout(orientation='vertical', size_hint_y=None, padding=[dp(12), dp(8)], spacing=dp(10))
        content.bind(minimum_height=content.setter('height'))

        header = SafeCard(size_hint_y=None, height=dp(40), padding=dp(6))
        header.add_widget(Label(text=fa('محاسبه واپاشی چشمه بر اساس روز'), bold=True, font_size=sp(13), color=(1.0, 0.5, 0.0, 1.0), **font_kw))
        content.add_widget(header)

        row = GridLayout(cols=2, spacing=dp(8), size_hint_y=None, height=dp(95))
        c_a0 = SafeCard(orientation='vertical', padding=dp(6))
        c_a0.add_widget(Label(text=fa('اکتیویته اولیه A0 (Ci)'), font_size=sp(11), color=(0.8, 0.8, 0.8, 1.0), **font_kw))
        self.in_a0 = SafeInput(text='80')
        self.in_a0.bind(text=self.calc)
        c_a0.add_widget(self.in_a0)
        row.add_widget(c_a0)

        c_d = SafeCard(orientation='vertical', padding=dp(6))
        c_d.add_widget(Label(text=fa('روزهای سپری شده (Days)'), font_size=sp(11), color=(0.8, 0.8, 0.8, 1.0), **font_kw))
        self.in_days = SafeInput(text='30')
        self.in_days.bind(text=self.calc)
        c_d.add_widget(self.in_days)
        row.add_widget(c_d)
        content.add_widget(row)

        self.res = SafeCard(orientation='vertical', bg_color=(0.04, 0.12, 0.08, 0.95), border_color=(0.10, 0.85, 0.40, 1.0), radius=12, size_hint_y=None, height=dp(130), padding=dp(10))
        self.res.add_widget(Label(text=fa('اکتیویته امروز چشمه (زنده)'), font_size=sp(12), color=(0.8, 0.9, 0.85, 1.0), **font_kw))
        self.lbl_at = Label(text=fa('-- Ci'), font_size=sp(28), bold=True, color=(0.15, 1.0, 0.45, 1.0), **font_kw)
        self.lbl_dec_info = Label(text=fa('درصد افت اکتیویته: --'), font_size=sp(11), color=(0.7, 0.8, 0.75, 1.0), **font_kw)
        self.res.add_widget(self.lbl_at)
        self.res.add_widget(self.lbl_dec_info)
        content.add_widget(self.res)

        scroll.add_widget(content)
        self.add_widget(scroll)
        self.calc()

    def calc(self, *args):
        try:
            a0 = float(self.in_a0.text.strip() or '0')
            days = float(self.in_days.text.strip() or '0')
            iso = ISOTOPES.get(self.app.current_source, ISOTOPES['Ir-192'])
            hl = iso['half_life']
            at = a0 * math.exp(-0.69315 * days / hl)
            pct = ((a0 - at) / a0 * 100.0) if a0 > 0 else 0
            self.lbl_at.text = fa(f"{at:.2f} Ci")
            self.lbl_dec_info.text = fa(f"چشمه {self.app.current_source} | افت: {pct:.1f}%")
        except Exception:
            pass


# ----------------- صفحه ۴: زمان پرتودهی -----------------
class ExposureScreen(Screen):
    def __init__(self, app, **kwargs):
        super(ExposureScreen, self).__init__(**kwargs)
        self.app = app
        font_kw = {'font_name': FONT_PATH} if FONT_PATH and os.path.exists(FONT_PATH) else {}

        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        content = BoxLayout(orientation='vertical', size_hint_y=None, padding=[dp(12), dp(8)], spacing=dp(10))
        content.bind(minimum_height=content.setter('height'))

        header = SafeCard(size_hint_y=None, height=dp(40), padding=dp(6))
        header.add_widget(Label(text=fa('محاسبه زمان اکسپوژر فیلم'), bold=True, font_size=sp(13), color=(1.0, 0.5, 0.0, 1.0), **font_kw))
        content.add_widget(header)

        row = GridLayout(cols=2, spacing=dp(8), size_hint_y=None, height=dp(95))
        c_th = SafeCard(orientation='vertical', padding=dp(6))
        c_th.add_widget(Label(text=fa('ضخامت لوله/فولاد (mm)'), font_size=sp(11), color=(0.8, 0.8, 0.8, 1.0), **font_kw))
        self.in_th = SafeInput(text='12')
        self.in_th.bind(text=self.calc)
        c_th.add_widget(self.in_th)
        row.add_widget(c_th)

        c_sfd = SafeCard(orientation='vertical', padding=dp(6))
        c_sfd.add_widget(Label(text=fa('فاصله SFD فیلم (cm)'), font_size=sp(11), color=(0.8, 0.8, 0.8, 1.0), **font_kw))
        self.in_sfd = SafeInput(text='50')
        self.in_sfd.bind(text=self.calc)
        c_sfd.add_widget(self.in_sfd)
        row.add_widget(c_sfd)
        content.add_widget(row)

        c_cur = SafeCard(orientation='vertical', size_hint_y=None, height=dp(85), padding=dp(6))
        c_cur.add_widget(Label(text=fa('اکتیویته فعلی چشمه (Ci)'), font_size=sp(11), color=(0.8, 0.8, 0.8, 1.0), **font_kw))
        self.in_cur = SafeInput(text='40')
        self.in_cur.bind(text=self.calc)
        c_cur.add_widget(self.in_cur)
        content.add_widget(c_cur)

        self.res = SafeCard(orientation='vertical', bg_color=(0.04, 0.12, 0.08, 0.95), border_color=(0.10, 0.85, 0.40, 1.0), radius=12, size_hint_y=None, height=dp(130), padding=dp(10))
        self.res.add_widget(Label(text=fa('زمان دقیق پرتودهی فیلم'), font_size=sp(12), color=(0.8, 0.9, 0.85, 1.0), **font_kw))
        self.lbl_t = Label(text=fa('--'), font_size=sp(26), bold=True, color=(0.15, 1.0, 0.45, 1.0), **font_kw)
        self.lbl_f_info = Label(text=fa('فیلم استاندارد رادیوگرافی کلاس I / II'), font_size=sp(11), color=(0.7, 0.8, 0.75, 1.0), **font_kw)
        self.res.add_widget(self.lbl_t)
        self.res.add_widget(self.lbl_f_info)
        content.add_widget(self.res)

        scroll.add_widget(content)
        self.add_widget(scroll)
        self.calc()

    def calc(self, *args):
        try:
            th = float(self.in_th.text.strip() or '12')
            sfd = float(self.in_sfd.text.strip() or '50')
            cur = max(0.1, float(self.in_cur.text.strip() or '40'))
            iso = ISOTOPES.get(self.app.current_source, ISOTOPES['Ir-192'])
            dist_factor = math.pow(sfd / 50.0, 2.0)
            thick_factor = math.pow(2.0, th / iso['hvl_fe'])
            sec = (iso['factor'] * thick_factor * dist_factor * 120.0) / (cur / 10.0)
            m = int(sec // 60)
            s = int(sec % 60)
            txt = f"{int(sec)} ثانیه" if m == 0 else f"{m} دقیقه و {s} ثانیه"
            self.lbl_t.text = fa(txt)
        except Exception:
            pass


# ----------------- صفحه ۵: شناسنامه ایزوتوپ -----------------
class IsotopeInfoScreen(Screen):
    def __init__(self, app, **kwargs):
        super(IsotopeInfoScreen, self).__init__(**kwargs)
        self.app = app
        font_kw = {'font_name': FONT_PATH} if FONT_PATH and os.path.exists(FONT_PATH) else {}

        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        content = BoxLayout(orientation='vertical', size_hint_y=None, padding=[dp(12), dp(8)], spacing=dp(8))
        content.bind(minimum_height=content.setter('height'))

        for iso_key, data in ISOTOPES.items():
            card = SafeCard(orientation='vertical', size_hint_y=None, height=dp(105), padding=dp(8), spacing=dp(3))
            card.add_widget(Label(text=fa(f"{data['name']} ({iso_key})"), bold=True, font_size=sp(13), color=(1.0, 0.5, 0.0, 1.0), halign='right', **font_kw))
            card.add_widget(Label(text=fa(f"ثابت گاما: {data['gamma']} R/h.Ci at 1m  |  میانگین انرژی: {data['energy']}"), font_size=sp(10), color=(0.8, 0.85, 0.9, 1.0), halign='right', **font_kw))
            card.add_widget(Label(text=fa(f"نیمه‌عمر: {data['half_life']} روز  |  HVL سرب: {data['hvl_pb']} mm"), font_size=sp(10), color=(0.8, 0.85, 0.9, 1.0), halign='right', **font_kw))
            card.add_widget(Label(text=fa(f"HVL فولاد: {data['hvl_fe']} mm"), font_size=sp(10), color=(0.6, 0.85, 0.7, 1.0), halign='right', **font_kw))
            content.add_widget(card)

        scroll.add_widget(content)
        self.add_widget(scroll)


# ----------------- کلاس اصلی برنامه -----------------
class NDTMainApp(App):
    def build(self):
        Window.clearcolor = (0.05, 0.06, 0.08, 1.0)
        self.title = 'رادیوگرافی صنعتی'
        self.current_source = 'Ir-192'
        self.bottom_buttons = {}

        root = BoxLayout(orientation='vertical')

        font_kw = {'font_name': FONT_PATH} if FONT_PATH and os.path.exists(FONT_PATH) else {}

        # هدر بالا با حاشیه و پدینگ کامل که حرف «ش» به هیچ وجه بریده نشود
        header = SafeCard(size_hint_y=None, height=dp(68), padding=[dp(14), dp(4), dp(22), dp(4)], spacing=dp(10))
        logo_f = get_asset('logo.png')
        if logo_f:
            header.add_widget(Image(source=logo_f, size_hint=(None, 1), width=dp(52)))

        t_box = BoxLayout(orientation='vertical', padding=[dp(8), 0, dp(4), 0])
        t_box.add_widget(Label(text=fa('شرکت رادیوگرافی صنعتی ایران'), font_size=sp(14), bold=True, color=(1.0, 0.50, 0.0, 1.0), halign='right', **font_kw))
        t_box.add_widget(Label(text=fa('محاسبات دوز، فاصله ایمن و پرتوگیری'), font_size=sp(10), color=(0.75, 0.80, 0.85, 1.0), halign='right', **font_kw))
        header.add_widget(t_box)
        root.add_widget(header)

        # مدیریت صفحات (ScreenManager)
        self.sm = ScreenManager(transition=FadeTransition(duration=0.15))
        self.sm.add_widget(SafetyScreen(self, name='screen_safety'))
        self.sm.add_widget(XRayScreen(self, name='screen_xray'))
        self.sm.add_widget(DecayScreen(self, name='screen_decay'))
        self.sm.add_widget(ExposureScreen(self, name='screen_exposure'))
        self.sm.add_widget(IsotopeInfoScreen(self, name='screen_info'))
        root.add_widget(self.sm)

        # ۵ دکمه ناوبری پایین صفحه (با قابلیت سوییچ واقعی و آنی صفحه)
        nav_bar = GridLayout(cols=5, size_hint_y=None, height=dp(54))
        tabs = [
            ('مرزبندی و حفاظ', 'screen_safety'),
            ('ایکس‌ری (X-Ray)', 'screen_xray'),
            ('واپاشی روز', 'screen_decay'),
            ('زمان پرتودهی', 'screen_exposure'),
            ('شناسنامه ایزوتوپ', 'screen_info')
        ]

        for i, (t_name, s_name) in enumerate(tabs):
            is_active = (i == 0)
            b = Button(
                text=fa(t_name),
                font_size=sp(10),
                bold=True,
                background_normal='',
                background_color=(1.0, 0.45, 0.0, 1.0) if is_active else (0.12, 0.14, 0.17, 1.0),
                color=(1, 1, 1, 1),
                **font_kw
            )
            b.bind(on_release=lambda inst, sn=s_name, btn=b: self.switch_tab(sn, btn))
            self.bottom_buttons[s_name] = b
            nav_bar.add_widget(b)

        root.add_widget(nav_bar)
        return root

    def switch_tab(self, screen_name, clicked_btn):
        self.sm.current = screen_name
        for sn, b in self.bottom_buttons.items():
            b.background_color = (1.0, 0.45, 0.0, 1.0) if sn == screen_name else (0.12, 0.14, 0.17, 1.0)

if __name__ == '__main__':
    NDTMainApp().run()
