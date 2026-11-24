from random import randint, uniform

from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Color, Ellipse, Rectangle
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

        self.info = Label(
            text="STAR DODGER",
            font_size="32sp",
            pos_hint={"center_x": 0.5, "center_y": 0.85},
        )
        self.add_widget(self.info)

        self.start_button = Button(
            text="START GAME",
            size_hint=(0.5, 0.12),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
        )
        self.start_button.bind(on_press=self.start_game)
        self.add_widget(self.start_button)

    def start_game(self, instance):
        # Avoid duplicate update loops if the player restarts quickly.
        Clock.unschedule(self.update)
        self.score = 0
        self.lives = 3
        self.player_x = 0.5
        self.asteroids.clear()
        self.stars.clear()
        self.game_started = True
        self.start_button.opacity = 0
        self.start_button.disabled = True
        self.info.text = "Score: 0 | Lives: 3"
        self.draw_game()
        Clock.schedule_interval(self.update, 1 / 60)

    def _move_player(self, touch):
        if self.width > 0:
            self.player_x = max(0.05, min(0.95, touch.x / self.width))
            self.draw_game()

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

        if randint(1, 35) == 1:
            self.asteroids.append([uniform(0.05, 0.95), 1.05])

        if randint(1, 45) == 1:
            self.stars.append([uniform(0.05, 0.95), 1.05])

        for asteroid in self.asteroids[:]:
            asteroid[1] -= dt * 0.35
            if asteroid[1] < 0:
                self.asteroids.remove(asteroid)
            elif (
                abs(asteroid[0] - self.player_x) < 0.07
                and asteroid[1] < 0.15
            ):
                self.asteroids.remove(asteroid)
                self.lives -= 1

        for star in self.stars[:]:
            star[1] -= dt * 0.3
            if star[1] < 0:
                self.stars.remove(star)
            elif (
                abs(star[0] - self.player_x) < 0.07
                and star[1] < 0.15
            ):
                self.stars.remove(star)
                self.score += 10

        if self.lives <= 0:
            self.game_started = False
            self.info.text = f"GAME OVER! Score: {self.score}"
            self.start_button.opacity = 1
            self.start_button.disabled = False
            self.draw_game()
            return False

        self.info.text = f"Score: {self.score} | Lives: {self.lives}"
        self.draw_game()
        return True

    def draw_game(self):
        self.canvas.clear()
        with self.canvas:
            Color(0.02, 0.02, 0.12)
            Rectangle(pos=self.pos, size=self.size)

            Color(0.1, 0.8, 1)
            Ellipse(
                pos=(self.player_x * self.width - 20, 35),
                size=(40, 40),
            )

            Color(1, 0.2, 0.2)
            for x, y in self.asteroids:
                Ellipse(
                    pos=(x * self.width - 15, y * self.height),
                    size=(30, 30),
                )

            Color(1, 0.85, 0.1)
            for x, y in self.stars:
                Ellipse(
                    pos=(x * self.width - 10, y * self.height),
                    size=(20, 20),
                )


class StarDodgerApp(App):
    def build(self):
        return StarDodger()


if __name__ == "__main__":
    StarDodgerApp().run()
