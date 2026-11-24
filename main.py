from random import randint, uniform

from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Color, Ellipse, Line, Rectangle, RoundedRectangle, Triangle
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.widget import Widget


class StarDodger(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.score = 0
        self.lives = 3
        self.player_x = 0.5
        self.asteroids = []
        self.stars = []
        self.game_started = False
        self.screen = "home"
        self.background_stars = [
            (uniform(0.02, 0.98), uniform(0.05, 0.98), uniform(1.0, 2.8))
            for _ in range(75)
        ]

        self.title = Label(
            text="[b]STAR[/b] [color=35d9ff]DODGER[/color]",
            markup=True,
            font_size="38sp",
            color=(0.92, 0.97, 1, 1),
            size_hint=(0.9, None),
            height=70,
            pos_hint={"center_x": 0.5, "center_y": 0.76},
        )
        self.subtitle = Label(
            text="DODGE THE ASTEROIDS. COLLECT THE STARS.",
            font_size="11sp",
            color=(0.55, 0.72, 0.86, 1),
            size_hint=(0.94, None),
            height=32,
            pos_hint={"center_x": 0.5, "center_y": 0.68},
        )
        self.info = Label(
            text="",
            font_size="17sp",
            bold=True,
            color=(0.9, 0.96, 1, 1),
            size_hint=(0.9, None),
            height=45,
            pos_hint={"center_x": 0.5, "top": 0.98},
        )
        self.hint = Label(
            text="MOVE YOUR FINGER TO STEER",
            font_size="11sp",
            color=(0.55, 0.72, 0.86, 1),
            size_hint=(0.9, None),
            height=30,
            pos_hint={"center_x": 0.5, "y": 0.04},
        )

        self.play_button = self.make_button("▶   PLAY", (0.62, 0.085))
        self.play_button.pos_hint = {"center_x": 0.5, "center_y": 0.48}
        self.play_button.bind(on_press=self.start_game)

        self.retry_button = self.make_button("PLAY AGAIN", (0.62, 0.085))
        self.retry_button.pos_hint = {"center_x": 0.5, "center_y": 0.43}
        self.retry_button.bind(on_press=self.start_game)

        self.add_widget(self.title)
        self.add_widget(self.subtitle)
        self.add_widget(self.info)
        self.add_widget(self.hint)
        self.add_widget(self.play_button)
        self.add_widget(self.retry_button)

        self.show_home()
        self.bind(size=self.redraw, pos=self.redraw)

    def make_button(self, text, size_hint):
        return Button(
            text=text,
            size_hint=size_hint,
            background_normal="",
            background_down="",
            background_color=(0.08, 0.68, 0.9, 1),
            color=(0.02, 0.06, 0.12, 1),
            font_size="17sp",
            bold=True,
        )

    def show_home(self):
        self.screen = "home"
        self.game_started = False
        Clock.unschedule(self.update)
        self.title.text = "[b]STAR[/b] [color=35d9ff]DODGER[/color]"
        self.subtitle.text = "DODGE THE ASTEROIDS. COLLECT THE STARS."
        self.info.text = ""
        self.hint.text = "MOVE YOUR FINGER TO STEER"
        self.play_button.text = "▶   PLAY"
        self.play_button.opacity = 1
        self.play_button.disabled = False
        self.retry_button.opacity = 0
        self.retry_button.disabled = True
        self.title.opacity = 1
        self.subtitle.opacity = 1
        self.hint.opacity = 1
        self.redraw()

    def start_game(self, instance):
        Clock.unschedule(self.update)
        self.score = 0
        self.lives = 3
        self.player_x = 0.5
        self.asteroids.clear()
        self.stars.clear()
        self.game_started = True
        self.screen = "game"
        self.title.opacity = 0
        self.subtitle.opacity = 0
        self.play_button.opacity = 0
        self.play_button.disabled = True
        self.retry_button.opacity = 0
        self.retry_button.disabled = True
        self.info.text = "SCORE  0        ♥  3"
        self.hint.text = "DRAG LEFT OR RIGHT TO MOVE"
        self.hint.opacity = 1
        self.redraw()
        Clock.schedule_interval(self.update, 1 / 60)

    def show_game_over(self):
        self.game_started = False
        self.screen = "over"
        Clock.unschedule(self.update)
        self.title.text = "[b]GAME[/b] [color=ff657a]OVER[/color]"
        self.title.opacity = 1
        self.subtitle.text = "YOUR FINAL SCORE"
        self.subtitle.opacity = 1
        self.info.text = f"[b]{self.score}[/b]  POINTS"
        self.info.markup = True
        self.info.font_size = "25sp"
        self.info.pos_hint = {"center_x": 0.5, "center_y": 0.56}
        self.play_button.opacity = 0
        self.play_button.disabled = True
        self.retry_button.opacity = 1
        self.retry_button.disabled = False
        self.hint.text = "KEEP GOING. YOU CAN BEAT THAT SCORE!"
        self.redraw()

    def _move_player(self, touch):
        if self.width > 0:
            self.player_x = max(0.06, min(0.94, (touch.x - self.x) / self.width))
            self.redraw()

    def on_touch_down(self, touch):
        if self.game_started:
            self._move_player(touch)
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.game_started:
            self._move_player(touch)
            return True
        return super().on_touch_move(touch)

    def update(self, dt):
        if not self.game_started:
            return False

        if randint(1, 30) == 1:
            self.asteroids.append([uniform(0.05, 0.95), 1.05])
        if randint(1, 42) == 1:
            self.stars.append([uniform(0.05, 0.95), 1.05])

        for asteroid in self.asteroids[:]:
            asteroid[1] -= dt * 0.35
            if asteroid[1] < -0.05:
                self.asteroids.remove(asteroid)
            elif abs(asteroid[0] - self.player_x) < 0.065 and asteroid[1] < 0.15:
                self.asteroids.remove(asteroid)
                self.lives -= 1

        for star in self.stars[:]:
            star[1] -= dt * 0.30
            if star[1] < -0.05:
                self.stars.remove(star)
            elif abs(star[0] - self.player_x) < 0.07 and star[1] < 0.15:
                self.stars.remove(star)
                self.score += 10

        if self.lives <= 0:
            self.show_game_over()
            return False

        self.info.text = f"SCORE  {self.score}        ♥  {self.lives}"
        self.redraw()
        return True

    def redraw(self, *args):
        self.canvas.clear()
        w, h = self.width, self.height
        if w <= 0 or h <= 0:
            return

        with self.canvas:
            # Deep-space background and soft nebula glow
            Color(0.012, 0.018, 0.065, 1)
            Rectangle(pos=self.pos, size=self.size)
            Color(0.035, 0.09, 0.19, 0.28)
            Ellipse(pos=(self.x + w * 0.08, self.y + h * 0.52),
                    size=(w * 0.85, h * 0.48))
            Color(0.12, 0.035, 0.20, 0.18)
            Ellipse(pos=(self.x + w * 0.35, self.y + h * 0.12),
                    size=(w * 0.8, h * 0.42))

            # Tiny background stars
            for sx, sy, radius in self.background_stars:
                Color(0.55, 0.78, 1, 0.35 + radius * 0.15)
                Ellipse(pos=(self.x + sx * w, self.y + sy * h),
                        size=(radius, radius))

            if self.screen == "home":
                # Decorative ship and orbit rings on the home screen
                cx, cy = self.x + w * 0.5, self.y + h * 0.28
                Color(0.10, 0.72, 1, 0.20)
                Line(circle=(cx, cy, min(w, h) * 0.16), width=1.2)
                Color(0.18, 0.82, 1, 0.12)
                Line(circle=(cx, cy, min(w, h) * 0.21), width=1)
                Color(0.10, 0.78, 1, 0.22)
                Ellipse(pos=(cx - 27, cy - 27), size=(54, 54))
                Color(0.35, 0.92, 1, 1)
                Triangle(points=[cx, cy + 39, cx - 25, cy - 25,
                                 cx, cy - 12, cx + 25, cy - 25])
                Color(0.88, 0.98, 1, 1)
                Ellipse(pos=(cx - 6, cy + 1), size=(12, 12))
                Color(0.10, 0.65, 1, 0.7)
                Ellipse(pos=(cx - 7, cy - 39), size=(14, 23))

            if self.screen == "game":
                # Player ship with glow and bright cockpit
                px = self.x + self.player_x * w
                py = self.y + h * 0.10
                Color(0.05, 0.65, 1, 0.22)
                Ellipse(pos=(px - 31, py - 17), size=(62, 62))
                Color(0.12, 0.78, 1, 1)
                Triangle(points=[px, py + 30, px - 23, py - 20,
                                 px, py - 10, px + 23, py - 20])
                Color(0.82, 0.97, 1, 1)
                Ellipse(pos=(px - 5, py + 3), size=(10, 10))
                Color(1, 0.45, 0.15, 0.9)
                Ellipse(pos=(px - 5, py - 26), size=(10, 17))

                # Asteroids
                for ax, ay in self.asteroids:
                    x, y = self.x + ax * w, self.y + ay * h
                    Color(1, 0.22, 0.30, 0.18)
                    Ellipse(pos=(x - 21, y - 6), size=(42, 42))
                    Color(0.88, 0.28, 0.32, 1)
                    Ellipse(pos=(x - 14, y), size=(28, 28))
                    Color(0.48, 0.12, 0.20, 1)
                    Ellipse(pos=(x - 5, y + 13), size=(6, 6))

                # Collectible stars
                for sx, sy in self.stars:
                    x, y = self.x + sx * w, self.y + sy * h
                    Color(1, 0.78, 0.12, 0.2)
                    Ellipse(pos=(x - 17, y - 3), size=(34, 34))
                    Color(1, 0.84, 0.22, 1)
                    Ellipse(pos=(x - 8, y + 1), size=(16, 16))

            # Subtle bottom edge
            Color(0.12, 0.68, 1, 0.35)
            Line(points=[self.x, self.y + 1, self.x + w, self.y + 1], width=1)


class StarDodgerApp(App):
    def build(self):
        self.title = "Star Dodger"
        return StarDodger()


if __name__ == "__main__":
    StarDodgerApp().run()
