import kivy
kivy.require('2.0.0')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.core.clipboard import Clipboard
from kivy.graphics import Color, Rectangle, Line
from kivy.core.window import Window
from kivy.clock import Clock
import requests

# Replace this with your API key
API_KEY = "******"
API_URL = "https://api.mistral.ai/v1/chat/completions" #change model if needed

def get_mistral_response(prompt):       # can change this if you wish to use any other api provider
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "mistral-large-2407",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }

    response = requests.post(API_URL, json=data, headers=headers)
    
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"Error: {response.status_code}, {response.text}"

class ColorButton(ButtonBehavior, BoxLayout):
    def __init__(self, hex_color, **kwargs):
        super().__init__(**kwargs)
        self.hex_color = hex_color
        self.size_hint_y = None
        self.height = 80
        self.padding = 10
        self.label = Label(text=hex_color, color=(1, 1, 1, 1))
        self.add_widget(self.label)

        with self.canvas.before:
            Color(*self.hex_to_rgba(hex_color))
            self.rect = Rectangle(pos=self.pos, size=self.size)
            Color(1, 1, 1, 1)
            self.outline = Line(rectangle=(self.x, self.y, self.width, self.height), width=2)

        self.bind(pos=self.update_graphics, size=self.update_graphics)

    def hex_to_rgba(self, hex_color):
        hex_color = hex_color.lstrip('#')
        lv = len(hex_color)
        rgb = tuple(int(hex_color[i:i + lv // 3], 16) / 255.0 for i in range(0, lv, lv // 3))
        return rgb + (1.0,)

    def update_graphics(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
        self.outline.rectangle = (self.x, self.y, self.width, self.height)

    def on_press(self):
        Clipboard.copy(self.hex_color)
        self.label.text = "Copied!"
        Clock.schedule_once(lambda dt: self.restore_label(), 1.0)

    def restore_label(self):
        self.label.text = self.hex_color

class CopyLabel(ButtonBehavior, Label):
    def __init__(self, hex_code, **kwargs):
        super().__init__(**kwargs)
        self.hex_code = hex_code
        self.text = f"Background color used: {hex_code}"
        self.color = (1, 1, 1, 1)
        self.original_text = self.text

    def on_press(self):
        Clipboard.copy(self.hex_code)
        self.text = "Copied background!"
        Clock.schedule_once(self.restore_text, 1.0)

    def restore_text(self, dt):
        self.text = self.original_text

class MoodifyLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 20
        self.spacing = 10

        self.input = TextInput(hint_text="Describe your mood...", size_hint=(1, 0.1), multiline=False)
        self.add_widget(self.input)

        self.button = Button(text="Generate Palette", size_hint=(1, 0.1))
        self.button.bind(on_press=self.generate_palette)
        self.add_widget(self.button)

        self.output = GridLayout(cols=1, spacing=10, size_hint_y=None)
        self.output.bind(minimum_height=self.output.setter('height'))

        self.scroll = ScrollView(size_hint=(1, 0.6))
        self.scroll.add_widget(self.output)
        self.add_widget(self.scroll)

        self.bg_button = None  # will be created dynamically
        self.theme_label = Label(text="", size_hint=(1, 0.05), color=(1, 1, 1, 1))
        self.add_widget(self.theme_label)

    def generate_palette(self, instance):
        mood_text = self.input.text.strip()
        if not mood_text:
            return

        prompt = f"""
        Given the mood \"{mood_text}\", generate:
        - 1 hex color code for the background
        - 5 hex color codes for a color palette representing this mood
        - A short creative 2-3 word name for this theme

        Respond exactly in this format:
        background: #HEX_BG
        palette: #HEX1, #HEX2, #HEX3, #HEX4, #HEX5
        theme: THEME_NAME
        """

        response = get_mistral_response(prompt)
        print("AI Response:\n", response)

        self.output.clear_widgets()

        if self.bg_button:
            self.remove_widget(self.bg_button)

        try:
            lines = response.strip().splitlines()
            bg_line = next(line for line in lines if line.startswith("background:"))
            palette_line = next(line for line in lines if line.startswith("palette:"))
            theme_line = next(line for line in lines if line.startswith("theme:"))
            
            bg_color = bg_line.split(":")[1].strip()
            palette_colors = [c.strip() for c in palette_line.split(":")[1].split(",")]
            theme_name = theme_line.split(":")[1].strip()

            Window.clearcolor = self.hex_to_rgba(bg_color)

            for color in palette_colors:
                color_button = ColorButton(color)
                self.output.add_widget(color_button)

            self.bg_button = CopyLabel(bg_color, size_hint=(1, 0.05))
            self.add_widget(self.bg_button, index=1)  # insert above theme label
            self.theme_label.text = f"Theme name: {theme_name}"

        except Exception as e:
            self.output.add_widget(Label(text=f"Error parsing response: {str(e)}"))

    def hex_to_rgba(self, hex_color):
        hex_color = hex_color.lstrip('#')
        lv = len(hex_color)
        rgb = tuple(int(hex_color[i:i + lv // 3], 16) / 255.0 for i in range(0, lv, lv // 3))
        return rgb + (1.0,)

class MoodifyApp(App):
    def build(self):
        return MoodifyLayout()

if __name__ == '__main__':
    MoodifyApp().run()
