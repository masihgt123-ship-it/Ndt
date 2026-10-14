from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.graphics import Color, RoundedRectangle, Ellipse
from kivy.core.text import LabelBase
from kivy.metrics import dp
from kivy.animation import Animation
import math

# ==================== ثبت فونت ====================
try:
    LabelBase.register(name='Vazir', fn_regular='Vazirmatn-Regular.ttf')
except:
    pass

class GlassCard(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(0.08, 0.09, 0.15, 0.92)
            self.bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(22)])
            Color(1, 0.85, 0.2, 0.35)
            self.border = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(22)])
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size
        self.border.pos = self.pos
        self.border.size = self.size


class NDTApp(App):
    def build(self):
        root = FloatLayout()

        # ===== پس‌زمینه تیره با افکت نور =====
        with root.canvas.before:
            Color(0.04, 0.05, 0.1, 1)
            RoundedRectangle(pos=root.pos, size=root.size)
            Color(1, 0.85, 0.2, 0.06)
            Ellipse(pos=(80, 650), size=(380, 380))
            Color(0.3, 0.7, 1, 0.08)
            Ellipse(pos=(250, 150), size=(450, 450))

        main = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(14))

        # ===== هدر بالا =====
        header = GlassCard(size_hint=(1, None), height=dp(52))
        header.add_widget(Label(text='📞 اطلاعات شرکت و تماس با ما',
                                font_name='Vazir', font_size=dp(15), color=(1, 1, 1, 0.95),
                                pos_hint={'center_y': 0.5}))
        main.add_widget(header)

        # ===== عنوان اصلی =====
        title_card = GlassCard(size_hint=(1, None), height=dp(95))
        title_card.add_widget(Label(text='محاسبه فاصله ایمن رادیوگرافی',
                                    font_name='Vazir', font_size=dp(21), bold=True,
                                    color=(1, 0.9, 0.3, 1), pos_hint={'center_y': 0.65}))
        title_card.add_widget(Label(text='NDT Gamma Radiation Calculator',
                                    font_name='Vazir', font_size=dp(13), color=(0.55, 0.8, 1, 1),
                                    pos_hint={'center_y': 0.25}))
        main.add_widget(title_card)

        # ===== انتخاب ایزوتوپ =====
        iso_card = GlassCard(size_hint=(1, None), height=dp(115))
        iso_card.add_widget(Label(text='اطلاعات ایزوتوپ پرتوزا  ⚛️',
                                  font_name='Vazir', font_size=dp(14), color=(0.85, 0.85, 0.9, 1),
                                  pos_hint={'center_y': 0.85}))

        self.iso_buttons = {}
        iso_box = BoxLayout(spacing=dp(8), padding=dp(8), size_hint=(1, None), height=dp(55),
                            pos_hint={'center_y': 0.35})
        for iso in ['Ir-192', 'Se-75', 'Co-60', 'Cs-137']:
            btn = Button(text=iso, font_name='Vazir', font_size=dp(15),
                         background_color=(0.12, 0.14, 0.22, 1), color=(1, 1, 1, 1))
            btn.bind(on_press=self.select_isotope)
            self.iso_buttons[iso] = btn
            iso_box.add_widget(btn)
        iso_card.add_widget(iso_box)
        main.add_widget(iso_card)

        # ===== ورودی‌ها =====
        input_card = GlassCard(size_hint=(1, None), height=dp(175))

        input_card.add_widget(Label(text='فعالیت ایزوتوپ (کیوری)', font_name='Vazir',
                                    font_size=dp(13), color=(0.75, 0.75, 0.8, 1),
                                    pos_hint={'center_y': 0.88}))
        self.activity = TextInput(text='70', font_name='Vazir', font_size=dp(20),
                                  background_color=(0.08, 0.09, 0.16, 1),
                                  foreground_color=(1, 0.92, 0.4, 1),
                                  size_hint=(1, None), height=dp(48), pos_hint={'center_y': 0.62})
        input_card.add_widget(self.activity)

        input_card.add_widget(Label(text='نرخ دوز مجاز (سیورت بر ساعت)', font_name='Vazir',
                                    font_size=dp(13), color=(0.75, 0.75, 0.8, 1),
                                    pos_hint={'center_y': 0.38}))
        self.dose = TextInput(text='2', font_name='Vazir', font_size=dp(20),
                              background_color=(0.08, 0.09, 0.16, 1),
                              foreground_color=(0.4, 0.95, 1, 1),
                              size_hint=(1, None), height=dp(48), pos_hint={'center_y': 0.12})
        input_card.add_widget(self.dose)
        main.add_widget(input_card)

        # ===== دکمه محاسبه =====
        calc_btn = Button(text='🧮  محاسبه فاصله ایمن (متر)',
                          font_name='Vazir', font_size=dp(18), bold=True,
                          background_color=(1, 0.85, 0.2, 1), color=(0.08, 0.08, 0.12, 1),
                          size_hint=(1, None), height=dp(58))
        calc_btn.bind(on_press=self.calculate)
        main.add_widget(calc_btn)

        # ===== نتیجه =====
        self.result_card = GlassCard(size_hint=(1, None), height=dp(135))
        self.result_label = Label(text='فاصله ایمن مرزی: -- متر',
                                  font_name='Vazir', font_size=dp(22), bold=True,
                                  color=(0.3, 0.95, 1, 1), pos_hint={'center_y': 0.65})
        self.detail_label = Label(text='', font_name='Vazir', font_size=dp(14),
                                  color=(1, 1, 1, 0.85), pos_hint={'center_y': 0.25})
        self.result_card.add_widget(self.result_label)
        self.result_card.add_widget(self.detail_label)
        main.add_widget(self.result_card)

        root.add_widget(main)

        # انتخاب پیش‌فرض Ir-192
        self.selected_iso = 'Ir-192'
        self.iso_buttons['Ir-192'].background_color = (1, 0.85, 0.2, 1)
        self.iso_buttons['Ir-192'].color = (0.08, 0.08, 0.12, 1)

        return root

    def select_isotope(self, instance):
        for iso, btn in self.iso_buttons.items():
            if btn == instance:
                btn.background_color = (1, 0.85, 0.2, 1)
                btn.color = (0.08, 0.08, 0.12, 1)
                self.selected_iso = iso
            else:
                btn.background_color = (0.12, 0.14, 0.22, 1)
                btn.color = (1, 1, 1, 1)

    def calculate(self, instance):
        try:
            activity = float(self.activity.text)
            dose = float(self.dose.text)
            gamma = {'Ir-192': 0.48, 'Se-75': 0.21, 'Co-60': 1.32, 'Cs-137': 0.33}.get(self.selected_iso, 0.5)

            distance = round(math.sqrt((activity * gamma) / dose), 2)

            self.result_label.text = f'فاصله ایمن مرزی: {distance} متر'
            self.detail_label.text = f'{self.selected_iso}  •  {activity} Ci'

            anim = Animation(opacity=0.3, duration=0.1) + Animation(opacity=1, duration=0.3)
            anim.start(self.result_card)

        except:
            self.result_label.text = 'لطفاً عدد معتبر وارد کنید'
            self.detail_label.text = ''


if __name__ == '__main__':
    NDTApp().run()
