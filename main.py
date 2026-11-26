import math
from random import randint, uniform

from kivy.app import App
from kivy.core.text import Label as CoreLabel
from kivy.clock import Clock
from kivy.graphics import Color, Ellipse, Line, Rectangle, RoundedRectangle, Triangle, PushMatrix, PopMatrix, Translate
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout


class StarDodger(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.score = 0
        self.lives = 3
        self.player_x = 0.5
        self.player_target_x = 0.5
        self.player_y = 0.14
        self.player_target_y = 0.14
        self.asteroids = []
        self.stars = []
        self.powerups = []
        self.powerup_spawn_time = 7.0
        self.shield_time = 0.0
        self.speed_boost_time = 0.0
        self.particles = []
        self.blasts = []
        self.bullets = []
        self.boss_shots = []
        self.enemies = []
        self.enemy_shots = []
        self.enemy_spawn_time = 4.0
        self.boss = None
        self.shot_time = 0.0
        self.boss_notice = 0.0
        self.level = 1
        self.level_time = 0.0
        self.score_time = 0.0
        self.shower_time = 0.0
        self.game_started = False
        self.screen = "home"
        self.difficulty = "Normal"
        self.best_score = 0
        self.background_stars = [
            (uniform(0.02, 0.98), uniform(0.02, 0.98), uniform(1.0, 2.8))
            for _ in range(150)
        ]
        self.background_drift = 0.0
        self.transition_time = 0.0
        self.transition_duration = 1.45

        self.title = self.make_label("[b]STAR[/b] [color=35d9ff]DODGER[/color]", 38, 0.77)
        self.title.markup = True
        self.subtitle = self.make_label("DODGE THE METEORS. COLLECT THE STARS.", 11, 0.68)
        self.info = self.make_label("", 17, 0.93)
        self.info.height = 58
        self.info.text_size = (None, None)
        self.info.halign = "center"
        self.info.valign = "middle"

        # Dedicated HUD labels keep lives, level, and score separate and readable.
        self.hud_level = self.make_hud_label("[b]LEVEL 1[/b]", 0.17)
        self.hud_lives = self.make_hud_label("[color=ff5875]♥ ♥ ♥[/color]", 0.50)
        self.hud_score = self.make_hud_label("[b]SCORE 0[/b]", 0.83)
        self.hint = self.make_label("TAP PLAY TO START", 11, 0.035)

        self.play_button = self.make_button("▶  PLAY", (0.64, 0.085), 0.49)
        self.play_button.bind(on_press=self.start_game)
        self.settings_button = self.make_button("⚙  SETTINGS", (0.64, 0.075), 0.37)
        self.settings_button.bind(on_press=self.show_settings)

        self.help_button = self.make_button("HOW TO PLAY", (0.64, 0.075), 0.25)
        self.help_button.bind(on_press=self.show_help)
        self.help_text = self.make_label(
            "DRAG LEFT OR RIGHT TO STEER\n"
            "DODGE METEORS AND ENEMY FIRE\n"
            "COLLECT STARS AND POWER-UPS\n"
            "DEFEAT A BOSS EVERY 5 LEVELS\n"
            "YOU HAVE 3 LIVES",
            15, 0.43
        )
        self.help_text.text_size = (self.width * 0.82, None)
        self.help_back_button = self.make_button("←  BACK TO MENU", (0.64, 0.075), 0.22)
        self.help_back_button.bind(on_press=self.show_home)

        self.retry_button = self.make_button("PLAY AGAIN", (0.64, 0.085), 0.43)
        self.retry_button.bind(on_press=self.start_game)
        self.home_button = self.make_button("MAIN MENU", (0.64, 0.075), 0.31)
        self.home_button.bind(on_press=self.show_home)

        self.difficulty_label = self.make_label("SELECT DIFFICULTY", 16, 0.57)
        self.difficulty_buttons = []
        for name, y in (("EASY", 0.46), ("NORMAL", 0.36), ("HARD", 0.26)):
            button = self.make_button(name, (0.64, 0.07), y)
            button.bind(on_press=lambda instance, value=name.title(): self.set_difficulty(value))
            self.difficulty_buttons.append(button)
        self.back_button = self.make_button("←  BACK", (0.64, 0.07), 0.15)
        self.back_button.bind(on_press=self.show_home)

        # Steering is touch-only: drag anywhere on the playfield.
        self.pause_button = self.make_button("", (0.17, 0.065), 0.82, 0.88)
        self.pause_button.background_color = (0, 0, 0, 0)
        self.pause_button.bind(on_press=self.pause_game)
        self.resume_button = self.make_button("▶  RESUME", (0.64, 0.08), 0.46)
        self.resume_button.bind(on_press=self.resume_game)
        self.pause_home_button = self.make_button("MAIN MENU", (0.64, 0.075), 0.34)
        self.pause_home_button.bind(on_press=self.show_home)

        for widget in (
            self.title, self.subtitle, self.info, self.hint,
            self.hud_level, self.hud_lives, self.hud_score,
            self.play_button, self.settings_button, self.help_button,
            self.help_text, self.help_back_button,
            self.retry_button, self.home_button, self.difficulty_label,
            *self.difficulty_buttons, self.back_button,
            self.pause_button, self.resume_button, self.pause_home_button
        ):
            self.add_widget(widget)

        self.bind(size=self.redraw, pos=self.redraw)
        self.show_home()

    def make_label(self, text, size, y):
        return Label(
            text=text, font_size=f"{size}sp", color=(0.9, 0.96, 1, 1),
            size_hint=(0.94, None), height=max(30, size * 2),
            pos_hint={"center_x": 0.5, "center_y": y},
            halign="center", valign="middle"
        )

    def make_hud_label(self, text, center_x):
        # Keep the HUD inside the safe screen area and give every value
        # a dark backing so it stays readable over every level background.
        label = Label(
            text=text, markup=True, font_size="20sp",
            color=(1, 1, 1, 1), bold=True,
            size_hint=(0.31, None), height=54,
            pos_hint={"center_x": center_x, "center_y": 0.925},
            halign="center", valign="middle"
        )
        label.text_size = (None, None)
        with label.canvas.before:
            Color(0.015, 0.035, 0.09, 0.92)
            panel = Rectangle(pos=label.pos, size=label.size)
        label.bind(pos=lambda instance, value: setattr(panel, "pos", value))
        label.bind(size=lambda instance, value: setattr(panel, "size", value))
        return label

    def update_hud(self):
        self.hud_level.text = f"[b]LEVEL {self.level}[/b]"
        hearts = " ".join("♥" for _ in range(max(0, self.lives)))
        self.hud_lives.text = f"[color=ff5875]{hearts or '0'}[/color]"
        self.hud_score.text = f"[b]SCORE {self.score}[/b]"

    def make_button(self, text, size_hint, y, x=0.5):
        return Button(
            text=text, size_hint=size_hint,
            pos_hint={"center_x": x, "center_y": y},
            background_normal="", background_down="",
            background_color=(0.08, 0.62, 0.88, 1),
            color=(0.02, 0.06, 0.12, 1),
            font_size="17sp", bold=True
        )

    def set_visible(self, widget, visible):
        widget.opacity = 1 if visible else 0
        widget.disabled = not visible

    def hide_game_controls(self):
        for widget in (self.pause_button,):
            self.set_visible(widget, False)

    def show_home(self, *args):
        Clock.unschedule(self.update)
        self.game_started = False
        self.screen = "home"
        self.title.text = "[b]STAR[/b] [color=35d9ff]DODGER[/color]"
        self.subtitle.text = "DODGE THE METEORS. COLLECT THE STARS."
        self.title.markup = True
        self.title.font_size = "38sp"
        self.subtitle.opacity = 1
        self.info.pos_hint = {"center_x": 0.5, "center_y": 0.56}
        self.info.height = 58
        self.info.font_size = "17sp"
        self.info.text = f"BEST SCORE  {self.best_score}" if self.best_score else "READY FOR YOUR NEXT RUN?"
        self.hint.text = "TAP PLAY TO START"
        # Home UI is rendered in the root canvas (not child widgets). This
        # avoids Android/Kivy widget stacking and first-frame layout issues.
        for widget in (
            self.title, self.subtitle, self.info, self.hint,
            self.hud_level, self.hud_lives, self.hud_score,
            self.play_button, self.settings_button, self.help_button,
            self.help_text, self.help_back_button, self.retry_button,
            self.home_button, self.difficulty_label, self.back_button,
            *self.difficulty_buttons, self.pause_button,
            self.resume_button, self.pause_home_button
        ):
            self.set_visible(widget, False)
        self.hide_game_controls()
        self.redraw()

    def show_settings(self, *args):
        Clock.unschedule(self.update)
        self.game_started = False
        self.screen = "settings"
        # Settings are rendered and hit-tested on the root canvas, just like
        # the home menu. This avoids Android child-button touch/layout issues.
        for widget in (self.title, self.subtitle, self.info, self.hint,
                       self.hud_level, self.hud_lives, self.hud_score,
                       self.play_button, self.settings_button, self.help_button,
                       self.help_text, self.help_back_button, self.retry_button,
                       self.home_button, self.difficulty_label, self.back_button,
                       *self.difficulty_buttons, self.pause_button,
                       self.resume_button, self.pause_home_button):
            self.set_visible(widget, False)
        self.hide_game_controls()
        self.redraw()

    def show_help(self, *args):
        Clock.unschedule(self.update)
        self.game_started = False
        self.screen = "help"
        # Help is also canvas-native so it remains readable and tappable
        # across Android screen sizes and touch configurations.
        for widget in (self.title, self.subtitle, self.info, self.hint,
                       self.hud_level, self.hud_lives, self.hud_score,
                       self.play_button, self.settings_button, self.help_button,
                       self.help_text, self.help_back_button, self.retry_button,
                       self.home_button, self.difficulty_label, self.back_button,
                       *self.difficulty_buttons, self.pause_button,
                       self.resume_button, self.pause_home_button):
            self.set_visible(widget, False)
        self.hide_game_controls()
        self.redraw()

    def set_difficulty(self, value):
        self.difficulty = value
        self.show_settings()

    def start_game(self, *args):
        Clock.unschedule(self.update)
        self.score = 0
        self.lives = 3
        self.player_x = 0.5
        self.player_target_x = 0.5
        self.player_y = 0.14
        self.player_target_y = 0.14
        self.asteroids.clear()
        self.stars.clear()
        self.powerups.clear()
        self.powerup_spawn_time = 7.0
        self.shield_time = 0.0
        self.speed_boost_time = 0.0
        self.particles.clear()
        self.blasts.clear()
        self.bullets.clear()
        self.boss_shots.clear()
        self.enemies.clear()
        self.enemy_shots.clear()
        self.enemy_spawn_time = 4.0
        self.boss = None
        self.shot_time = 0.0
        self.boss_notice = 0.0
        self.level = 1
        self.level_time = 0.0
        self.score_time = 0.0
        self.shower_time = 0.0
        self.game_started = True
        self.screen = "game"

        for widget in (self.title, self.subtitle, self.play_button,
                       self.settings_button, self.retry_button, self.home_button,
                       self.difficulty_label, self.back_button, self.resume_button,
                       self.pause_home_button):
            self.set_visible(widget, False)
        for button in self.difficulty_buttons:
            self.set_visible(button, False)
        self.set_visible(self.info, False)
        # The canvas HUD is the single source of truth during gameplay.
        for hud in (self.hud_level, self.hud_lives, self.hud_score):
            self.set_visible(hud, False)
        self.update_hud()
        self.set_visible(self.hint, True)
        self.set_visible(self.info, False)
        for hud in (self.hud_level, self.hud_lives, self.hud_score):
            self.set_visible(hud, True)
        self.update_hud()
        self.set_visible(self.pause_button, True)
        self.info.text = "LEVEL 1       ♥ 3 LIVES\nSCORE 0"
        self.hint.text = "DRAG ANYWHERE TO FLY  •  LEFT / RIGHT / UP / DOWN"
        self.redraw()
        Clock.schedule_interval(self.update, 1 / 60)

    def pause_game(self, *args):
        if self.screen != "game":
            return
        Clock.unschedule(self.update)
        self.game_started = False
        self.screen = "paused"
        self.set_visible(self.pause_button, False)
        self.set_visible(self.title, True)
        self.title.text = "[b]PAUSED[/b]"
        self.title.markup = True
        self.set_visible(self.subtitle, True)
        self.subtitle.text = "TAKE A BREATHER"
        self.set_visible(self.info, True)
        for hud in (self.hud_level, self.hud_lives, self.hud_score):
            self.set_visible(hud, False)
        self.info.text = f"LEVEL {self.level}       {self.lives} LIVES\nSCORE {self.score}"
        self.set_visible(self.hint, False)
        self.set_visible(self.resume_button, True)
        self.set_visible(self.pause_home_button, True)
        self.redraw()

    def resume_game(self, *args):
        if self.screen != "paused":
            return
        self.screen = "game"
        self.game_started = True
        self.set_visible(self.title, False)
        self.set_visible(self.subtitle, False)
        self.set_visible(self.resume_button, False)
        self.set_visible(self.pause_home_button, False)
        self.set_visible(self.hint, True)
        self.set_visible(self.pause_button, True)
        Clock.schedule_interval(self.update, 1 / 60)

    def game_over(self):
        Clock.unschedule(self.update)
        self.game_started = False
        self.screen = "over"
        self.is_new_best = self.score > self.best_score
        self.best_score = max(self.best_score, self.score)
        # The fail screen is drawn directly on the game canvas for consistent
        # sizing on Android devices; only the two action buttons remain widgets.
        for widget in (self.title, self.subtitle, self.info, self.hint):
            self.set_visible(widget, False)
        for hud in (self.hud_level, self.hud_lives, self.hud_score):
            self.set_visible(hud, False)
        self.retry_button.text = "↻  PLAY AGAIN"
        self.retry_button.pos_hint = {"center_x": 0.5, "center_y": 0.405}
        self.home_button.text = "⌂  MAIN MENU"
        self.home_button.pos_hint = {"center_x": 0.5, "center_y": 0.285}
        self.set_visible(self.retry_button, True)
        self.set_visible(self.home_button, True)
        self.set_visible(self.play_button, False)
        self.set_visible(self.settings_button, False)
        self.set_visible(self.help_button, False)
        self.hide_game_controls()
        self.redraw()

    def draw_game_over(self, w, h):
        panel_w, panel_h = w * 0.86, h * 0.64
        panel_x = self.x + (w - panel_w) * 0.5
        panel_y = self.y + h * 0.17
        Color(1.0, 0.25, 0.52, 0.20)
        RoundedRectangle(pos=(panel_x - 7, panel_y - 7),
                         size=(panel_w + 14, panel_h + 14), radius=[38])
        Color(0.018, 0.025, 0.09, 0.97)
        RoundedRectangle(pos=(panel_x, panel_y),
                         size=(panel_w, panel_h), radius=[34])
        Color(1.0, 0.42, 0.64, 0.95)
        Line(rounded_rectangle=(panel_x, panel_y, panel_w, panel_h, 34), width=2)
        self.draw_centered_canvas_text("OH NO, SPACE CADET!", self.x + w * 0.5,
                                       self.y + h * 0.79, max(25, w * 0.064),
                                       (1.0, 0.60, 0.72, 1))
        self.draw_centered_canvas_text("THAT WAS ONE WILD RIDE!",
                                       self.x + w * 0.5, self.y + h * 0.715,
                                       max(11, w * 0.027), (0.60, 0.86, 1, 1))
        score_y = self.y + h * 0.575
        Color(0.10, 0.62, 1, 0.20)
        RoundedRectangle(pos=(self.x + w * 0.20, score_y - h * 0.080),
                         size=(w * 0.60, h * 0.16), radius=[30])
        Color(0.45, 0.88, 1, 0.8)
        Line(rounded_rectangle=(self.x + w * 0.20, score_y - h * 0.080,
                                w * 0.60, h * 0.16, 30), width=1.2)
        self.draw_centered_canvas_text("YOUR SCORE", self.x + w * 0.5,
                                       score_y + h * 0.037, max(12, w * 0.031),
                                       (0.66, 0.90, 1, 1))
        self.draw_centered_canvas_text(str(self.score), self.x + w * 0.5,
                                       score_y - h * 0.025, max(34, w * 0.10),
                                       (1, 1, 1, 1))
        stat_y = self.y + h * 0.405
        self.draw_centered_canvas_text(f"LEVEL {self.level}  •  {self.lives} LIVES LEFT",
                                       self.x + w * 0.5, stat_y,
                                       max(13, w * 0.033), (0.72, 0.92, 1, 1))
        best_label = "NEW PERSONAL BEST!  ✨" if self.is_new_best else f"BEST SCORE  {self.best_score}"
        best_color = (1.0, 0.84, 0.40, 1) if self.is_new_best else (0.50, 1.0, 0.82, 1)
        self.draw_centered_canvas_text(best_label, self.x + w * 0.5,
                                       self.y + h * 0.335,
                                       max(13, w * 0.033), best_color)

    def shift_player(self, amount):
        if self.screen == "game":
            # Arrow taps set a destination; glide toward it instead of teleporting.
            self.player_target_x = max(0.07, min(0.93, self.player_target_x + amount))

    def move_player_to(self, x, y):
        if self.width > 0 and self.height > 0:
            # Direct touch steering: keep the ship centered under the finger
            # with no easing lag, while clamping it inside the playfield.
            nx = max(0.055, min(0.945, (x - self.x) / self.width))
            ny = max(0.10, min(0.90, (y - self.y) / self.height))
            self.player_target_x = self.player_x = nx
            self.player_target_y = self.player_y = ny
            self.redraw()

    def on_touch_down(self, touch):
        # All menu screens use explicit canvas hit zones for reliable Android taps.
        if self.screen in ("home", "settings", "help") and self.height > 0 and self.width > 0:
            nx = (touch.x - self.x) / self.width
            ny = (touch.y - self.y) / self.height
            if 0.16 <= nx <= 0.84:
                if self.screen == "home":
                    if 0.445 <= ny <= 0.535:
                        self.start_game()
                        return True
                    if 0.325 <= ny <= 0.415:
                        self.show_settings()
                        return True
                    if 0.205 <= ny <= 0.295:
                        self.show_help()
                        return True
                elif self.screen == "settings":
                    if 0.415 <= ny <= 0.505:
                        self.set_difficulty("Easy")
                        return True
                    if 0.315 <= ny <= 0.405:
                        self.set_difficulty("Normal")
                        return True
                    if 0.215 <= ny <= 0.305:
                        self.set_difficulty("Hard")
                        return True
                    if 0.105 <= ny <= 0.195:
                        self.show_home()
                        return True
                elif self.screen == "help" and 0.105 <= ny <= 0.195:
                    self.show_home()
                    return True
            return True
        # Let gameplay controls (including pause) receive their tap first.
        if super().on_touch_down(touch):
            return True
        if self.screen == "game":
            self.move_player_to(touch.x, touch.y)
            touch.grab(self)
            return True
        return False

    def on_touch_move(self, touch):
        if self.screen == "game" and touch.grab_current is self:
            self.move_player_to(touch.x, touch.y)
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            return True
        return super().on_touch_up(touch)

    def explode(self, x, y, count=14):
        self.blasts.append([x, y, 0.0])
        for _ in range(count):
            angle = uniform(0, math.tau)
            speed = uniform(0.10, 0.46)
            self.particles.append([
                x, y, math.cos(angle) * speed, math.sin(angle) * speed,
                uniform(0.2, 0.6), uniform(1.5, 4.5)
            ])

    def circle_hits_ship(self, cx, cy, radius):
        """Pixel-space circle vs. the visible ship silhouette; glow is ignored."""
        w, h = self.width, self.height
        px = self.x + self.player_x * w
        py = self.y + self.player_y * h
        # Outer contour of the rendered wings and armored fuselage.
        polygon = [
            (px, py + 35), (px - 28, py - 19), (px - 18, py - 23),
            (px - 34, py - 15), (px - 18, py - 5), (px - 8, py - 17),
            (px, py - 17), (px + 8, py - 17), (px + 18, py - 5),
            (px + 34, py - 15), (px + 18, py - 23), (px + 28, py - 19)
        ]
        inside = False
        j = len(polygon) - 1
        for i, (ax, ay) in enumerate(polygon):
            bx, by = polygon[j]
            if ((ay > cy) != (by > cy)):
                cross_x = (bx - ax) * (cy - ay) / ((by - ay) or 1e-12) + ax
                if cx < cross_x:
                    inside = not inside
            j = i
        if inside:
            return True
        r2 = radius * radius
        for i, (ax, ay) in enumerate(polygon):
            bx, by = polygon[(i + 1) % len(polygon)]
            dx, dy = bx - ax, by - ay
            length2 = dx * dx + dy * dy
            t = 0.0 if length2 == 0 else max(0.0, min(1.0,
                ((cx - ax) * dx + (cy - ay) * dy) / length2))
            qx, qy = ax + t * dx, ay + t * dy
            if (cx - qx) ** 2 + (cy - qy) ** 2 <= r2:
                return True
        return False

    def update(self, dt):
        if not self.game_started or self.screen != "game":
            return False
        dt = min(dt, 0.05)
        self.level_time += dt
        self.score_time += dt
        self.background_drift = (self.background_drift + dt * 0.018) % 1.0
        self.transition_time = max(0.0, self.transition_time - dt)
        # Position is updated directly by touch events for zero-easing input.
        self.player_x = self.player_target_x
        self.player_y = self.player_target_y
        self.shower_time = max(0.0, self.shower_time - dt)
        self.shield_time = max(0.0, self.shield_time - dt)
        self.speed_boost_time = max(0.0, self.speed_boost_time - dt)
        self.powerup_spawn_time -= dt
        if self.powerup_spawn_time <= 0:
            self.powerups.append([uniform(0.10, 0.90), 1.08, randint(0, 2)])
            self.powerup_spawn_time = uniform(13.0, 19.0)

        if self.level_time >= 20:
            self.level_time -= 20
            self.level += 1
            self.transition_time = self.transition_duration
            self.score += 25
            self.shower_time = 4.5
            if self.level % 5 == 0 and self.boss is None:
                boss_index = self.level // 5 - 1
                boss_hp = 12 + boss_index * 7
                boss_type = boss_index % 5
                self.boss = [0.5, 0.80, boss_hp, boss_hp, 0.0, 0.0, boss_type]
                self.boss_notice = 3.0
                self.boss_shots.clear()

        if self.score_time >= 1:
            points = int(self.score_time)
            self.score += points
            self.score_time -= points

        base_spawn = {"Easy": 50, "Normal": 38, "Hard": 29}[self.difficulty]
        spawn_chance = max(8, base_spawn - self.level * 2 - (7 if self.shower_time > 0 else 0))
        base_speed = {"Easy": 0.25, "Normal": 0.32, "Hard": 0.40}[self.difficulty]
        speed = min(0.95, base_speed + self.level * 0.022)
        self.boss_notice = max(0.0, self.boss_notice - dt)

        if self.boss is None and randint(1, spawn_chance) == 1:
            self.asteroids.append([
                uniform(0.06, 0.94), 1.08, uniform(0.95, 1.5),
                speed * uniform(0.82, 1.2), randint(0, 3), uniform(0, math.tau)
            ])
        if self.boss is None and self.shower_time > 0 and randint(1, 7) == 1:
            self.asteroids.append([uniform(0.06, 0.94), 1.08, uniform(0.85, 1.25), speed * 1.35, randint(0, 3), uniform(0, math.tau)])
        if randint(1, max(18, 46 - self.level)) == 1:
            self.stars.append([uniform(0.06, 0.94), 1.06, uniform(0, math.tau)])

        self.shot_time += dt
        if self.shot_time >= 0.42:
            self.shot_time = 0.0
            self.bullets.append([self.player_x, min(1.04, self.player_y + 0.08)])

        for bullet in self.bullets[:]:
            bullet[1] += dt * 1.05
            if bullet[1] > 1.12:
                self.bullets.remove(bullet)

        # Regular enemy fighters begin appearing after level 5.
        if self.level > 5:
            self.enemy_spawn_time -= dt
            if self.enemy_spawn_time <= 0 and len(self.enemies) < min(4, 1 + self.level // 8):
                enemy_type = randint(0, 2)
                enemy_hp = 2 + min(4, (self.level - 6) // 5)
                self.enemies.append([
                    uniform(0.12, 0.88), uniform(0.78, 1.02),
                    enemy_hp, enemy_hp, uniform(0, math.tau), uniform(0.7, 1.5),
                    enemy_type
                ])
                self.enemy_spawn_time = uniform(3.5, 6.5) * max(0.58, 1 - (self.level - 6) * 0.025)
        else:
            self.enemy_spawn_time = 4.0

        for enemy in self.enemies[:]:
            enemy_type = int(enemy[6])
            enemy[4] += dt
            enemy[0] += math.sin(enemy[4] * (1.1 + enemy_type * 0.35)) * dt * (0.10 + self.level * 0.002)
            enemy[0] = max(0.08, min(0.92, enemy[0]))
            enemy[1] -= dt * (0.055 + self.level * 0.0025)
            enemy[5] -= dt
            if enemy[5] <= 0:
                enemy[5] = uniform(1.1, 1.9) * max(0.62, 1 - (self.level - 6) * 0.018)
                dx = max(-0.30, min(0.30, (self.player_x - enemy[0]) * 0.42))
                shot_speed = 0.30 + self.level * 0.009
                self.enemy_shots.append([enemy[0], enemy[1] - 0.035, dx, -shot_speed])
                if enemy_type == 2:
                    self.enemy_shots.append([enemy[0], enemy[1] - 0.035, dx - 0.13, -shot_speed * 0.88])
                    self.enemy_shots.append([enemy[0], enemy[1] - 0.035, dx + 0.13, -shot_speed * 0.88])
            if enemy[1] < -0.12:
                self.enemies.remove(enemy)
                continue
            for bullet in self.bullets[:]:
                if abs(bullet[0] - enemy[0]) < 0.075 and abs(bullet[1] - enemy[1]) < 0.065:
                    self.bullets.remove(bullet)
                    enemy[2] -= 1
                    self.explode(enemy[0], enemy[1], 4)
                    if enemy[2] <= 0:
                        self.score += 75 + self.level * 5
                        self.explode(enemy[0], enemy[1], 18)
                        self.enemies.remove(enemy)
                    break
            if enemy not in self.enemies:
                continue
            if self.circle_hits_ship(self.x + enemy[0] * self.width,
                                     self.y + enemy[1] * self.height, 13):
                self.enemies.remove(enemy)
                if self.shield_time > 0:
                    self.shield_time = 0.0
                    self.explode(enemy[0], enemy[1], 20)
                else:
                    self.lives -= 1
                    self.explode(enemy[0], enemy[1], 18)

        for shot in self.enemy_shots[:]:
            shot[0] += shot[2] * dt
            shot[1] += shot[3] * dt
            if shot[1] < -0.08 or shot[0] < -0.08 or shot[0] > 1.08:
                self.enemy_shots.remove(shot)
            elif self.circle_hits_ship(self.x + shot[0] * self.width,
                                       self.y + shot[1] * self.height, 8):
                self.enemy_shots.remove(shot)
                if self.shield_time > 0:
                    self.shield_time = 0.0
                    self.explode(shot[0], shot[1], 18)
                else:
                    self.lives -= 1
                    self.explode(shot[0], shot[1], 14)

        if self.boss is not None:
            boss = self.boss
            boss_type = int(boss[6]) if len(boss) > 6 else 0
            boss[4] += dt
            boss[0] = 0.5 + math.sin(boss[4] * (0.72 + boss_type * 0.10)) * (0.25 if boss_type == 2 else 0.31)
            boss[5] += dt
            attack_interval = max(0.34, 1.12 - (self.level // 5) * 0.075)
            if boss[5] >= attack_interval:
                boss[5] = 0.0
                difficulty_boost = {"Easy": 0.88, "Normal": 1.0, "Hard": 1.14}[self.difficulty]
                shot_speed = (0.25 + self.level * 0.012) * difficulty_boost
                origin_y = boss[1] - 0.08
                if boss_type == 0:
                    # Scout Destroyer: one shot leads the player's current position.
                    dx = max(-0.42, min(0.42, (self.player_x - boss[0]) * 0.72))
                    self.boss_shots.append([boss[0], origin_y, dx, -shot_speed])
                elif boss_type == 1:
                    # Twin Blaster: a wide five-shot fan.
                    for offset in (-0.34, -0.17, 0.0, 0.17, 0.34):
                        self.boss_shots.append([boss[0], origin_y, offset, -shot_speed])
                elif boss_type == 2:
                    # Meteor Titan: drops a short, staggered meteor volley.
                    for lane in (-0.20, 0.0, 0.20):
                        self.asteroids.append([
                            max(0.06, min(0.94, boss[0] + lane + uniform(-0.045, 0.045))),
                            origin_y, uniform(1.05, 1.35), shot_speed * 0.82,
                            randint(0, 3), uniform(0, math.tau)
                        ])
                elif boss_type == 3:
                    # Void Reaper: rotating spiral volley.
                    spin = boss[4] * 1.7
                    for index in range(4):
                        angle = spin + index * (math.tau / 4)
                        self.boss_shots.append([
                            boss[0], origin_y,
                            math.cos(angle) * shot_speed * 0.78,
                            -abs(math.sin(angle) * shot_speed * 0.55) - shot_speed * 0.42
                        ])
                else:
                    # Galaxy Overlord: alternates a targeted blast and a dense fan.
                    if int(boss[4] / 2.4) % 2 == 0:
                        dx = max(-0.48, min(0.48, (self.player_x - boss[0]) * 0.82))
                        self.boss_shots.append([boss[0], origin_y, dx, -shot_speed * 1.12])
                    else:
                        for offset in (-0.30, -0.15, 0.0, 0.15, 0.30):
                            self.boss_shots.append([boss[0], origin_y, offset, -shot_speed * 0.92])

            for bullet in self.bullets[:]:
                if abs(bullet[0] - boss[0]) < 0.13 and abs(bullet[1] - boss[1]) < 0.12:
                    self.bullets.remove(bullet)
                    boss[2] -= 1
                    self.explode(boss[0] + uniform(-0.08, 0.08), boss[1], 5)
                    if boss[2] <= 0:
                        self.score += 250 + self.level * 20
                        self.explode(boss[0], boss[1], 55)
                        self.boss = None
                        self.boss_shots.clear()
                        self.shower_time = 3.0
                        break

        # Boss projectiles now need to overlap the ship's smaller collision zone.
        for shot in self.boss_shots[:]:
            # Keep a short fading position history so each plasma bolt leaves
            # a curved, motion-following energy trail instead of a static line.
            if len(shot) < 5:
                shot.append([])
            trail = shot[4]
            for point in trail:
                point[2] -= dt * 2.8
            trail[:] = [point for point in trail if point[2] > 0]
            trail.append([shot[0], shot[1], 1.0])
            if len(trail) > 10:
                trail.pop(0)
            shot[0] += shot[2] * dt
            shot[1] += shot[3] * dt
            if shot[1] < -0.08 or shot[0] < -0.08 or shot[0] > 1.08:
                self.boss_shots.remove(shot)
            elif self.circle_hits_ship(
                    self.x + shot[0] * self.width,
                    self.y + shot[1] * self.height, 8):
                self.boss_shots.remove(shot)
                if self.shield_time > 0:
                    self.shield_time = 0.0
                    self.explode(shot[0], shot[1], 22)
                else:
                    self.lives -= 1
                    self.explode(shot[0], shot[1], 16)

        # Use a tighter collision box than the visible ship and meteor glow.
        # The meteor must overlap both horizontally and vertically to cause damage.
        for meteor in self.asteroids[:]:
            meteor[1] -= dt * meteor[3]
            if meteor[1] < -0.12:
                self.asteroids.remove(meteor)
            elif self.circle_hits_ship(
                    self.x + meteor[0] * self.width,
                    self.y + meteor[1] * self.height, 15 * meteor[2]):
                self.asteroids.remove(meteor)
                if self.shield_time > 0:
                    self.shield_time = 0.0
                    self.explode(meteor[0], meteor[1], 26)
                else:
                    self.lives -= 1
                    self.explode(meteor[0], meteor[1], 20)

        for star in self.stars[:]:
            star[1] -= dt * 0.3
            if len(star) < 3:
                star.append(0.0)
            star[2] = (star[2] + dt * 5.5) % math.tau
            if star[1] < -0.08:
                self.stars.remove(star)
            elif self.circle_hits_ship(
                    self.x + star[0] * self.width,
                    self.y + star[1] * self.height, 11):
                self.stars.remove(star)
                self.score += 15
                self.explode(star[0], star[1], 9)

        for pickup in self.powerups[:]:
            pickup[1] -= dt * 0.24
            if pickup[1] < -0.08:
                self.powerups.remove(pickup)
            elif self.circle_hits_ship(
                    self.x + pickup[0] * self.width,
                    self.y + pickup[1] * self.height, 12):
                self.powerups.remove(pickup)
                if pickup[2] == 0:
                    self.shield_time = 7.0
                    self.explode(pickup[0], pickup[1], 20)
                elif pickup[2] == 1:
                    self.score += 100
                    self.explode(pickup[0], pickup[1], 18)
                else:
                    self.speed_boost_time = 6.0
                    self.explode(pickup[0], pickup[1], 20)

        for blast in self.blasts[:]:
            blast[2] += dt
            if blast[2] > 0.48:
                self.blasts.remove(blast)

        for particle in self.particles[:]:
            particle[0] += particle[2] * dt
            particle[1] += particle[3] * dt
            particle[4] -= dt
            if particle[4] <= 0:
                self.particles.remove(particle)

        if self.lives <= 0:
            self.game_over()
            return False

        boss_names = ("SCOUT DESTROYER", "TWIN BLASTER", "METEOR TITAN", "VOID REAPER", "GALAXY OVERLORD")
        boss_text = f"   {boss_names[int(self.boss[6]) % 5]}  {self.boss[2]}/{self.boss[3]}" if self.boss else ""
        self.info.text = f"LEVEL {self.level}       ♥ {self.lives} LIVES{boss_text}\nSCORE {self.score}"
        if self.boss_notice > 0:
            self.hint.text = "⚠  BOSS INCOMING!"
        elif self.shield_time > 0:
            self.hint.text = f"SHIELD ACTIVE  {self.shield_time:.1f}s"
        elif self.speed_boost_time > 0:
            self.hint.text = f"SPEED BOOST  {self.speed_boost_time:.1f}s"
        else:
            self.hint.text = "DEFEAT THE BOSS!" if self.boss else "DODGE METEORS • COLLECT STARS • GRAB POWER-UPS"
        self.redraw()
        return True

    def draw_canvas_text(self, text, x, y, font_size, color):
        label = CoreLabel(text=text, font_size=font_size, bold=True, color=color)
        label.refresh()
        texture = label.texture
        Color(1, 1, 1, 1)
        Rectangle(texture=texture, pos=(x, y), size=texture.size)

    def draw_centered_canvas_text(self, text, center_x, center_y, font_size, color,
                                   max_width=None, max_height=None):
        # Shrink text to fit its card/button bounds on narrow phones.
        fitted_size = float(font_size)
        label = CoreLabel(text=text, font_size=fitted_size, bold=True, color=color)
        label.refresh()
        while fitted_size > 8 and (
                (max_width is not None and label.texture.width > max_width) or
                (max_height is not None and label.texture.height > max_height)):
            fitted_size -= 1
            label = CoreLabel(text=text, font_size=fitted_size, bold=True, color=color)
            label.refresh()
        texture = label.texture
        # Subtle offset shadow keeps text readable over bright backgrounds.
        Color(0.005, 0.012, 0.045, 0.72)
        Rectangle(texture=texture,
                  pos=(center_x - texture.width / 2 + 1.5,
                       center_y - texture.height / 2 - 1.5),
                  size=texture.size)
        Color(1, 1, 1, 1)
        Rectangle(texture=texture,
                  pos=(center_x - texture.width / 2, center_y - texture.height / 2),
                  size=texture.size)

    def draw_home_menu(self, w, h):
        # Playful rounded-glass home card with colorful pill buttons.
        panel_w, panel_h = w * 0.84, h * 0.68
        panel_x, panel_y = self.x + (w - panel_w) / 2, self.y + h * 0.11
        Color(0.12, 0.55, 1, 0.18)
        RoundedRectangle(pos=(panel_x - 7, panel_y - 7),
                         size=(panel_w + 14, panel_h + 14), radius=[38])
        Color(0.018, 0.035, 0.105, 0.88)
        RoundedRectangle(pos=(panel_x, panel_y), size=(panel_w, panel_h), radius=[34])
        Color(0.30, 0.82, 1, 0.95)
        Line(rounded_rectangle=(panel_x, panel_y, panel_w, panel_h, 34), width=2)
        Color(0.75, 0.94, 1, 0.18)
        Line(points=[panel_x + 34, panel_y + panel_h - 12,
                     panel_x + panel_w - 34, panel_y + panel_h - 12], width=2)

        self.draw_centered_canvas_text("STAR DODGER", self.x + w * 0.5,
                                       self.y + h * 0.80, max(32, w * 0.078),
                                       (1.0, 0.94, 0.55, 1))
        self.draw_centered_canvas_text("DODGE • COLLECT • EXPLORE",
                                       self.x + w * 0.5, self.y + h * 0.70,
                                       max(11, w * 0.028), (0.54, 0.91, 1, 1))
        status = f"BEST SCORE  {self.best_score}" if self.best_score else "READY FOR YOUR NEXT RUN?"
        bx, by, bw, bh = self.x + w * 0.25, self.y + h * 0.535, w * 0.50, h * 0.065
        Color(0.20, 0.72, 1, 0.18)
        RoundedRectangle(pos=(bx, by), size=(bw, bh), radius=[22])
        self.draw_centered_canvas_text(status, self.x + w * 0.5,
                                       by + bh * 0.5, max(12, w * 0.029),
                                       (0.88, 0.96, 1, 1),
                                       max_width=bw * 0.90, max_height=bh * 0.72)

        buttons = (
            ("LET'S PLAY!  ✦", 0.49, (0.10, 0.66, 0.98, 1), (0.55, 0.90, 1, 1)),
            ("SETTINGS  ⚙", 0.37, (0.36, 0.27, 0.82, 1), (0.76, 0.67, 1, 1)),
            ("HOW TO PLAY  ★", 0.25, (0.08, 0.60, 0.54, 1), (0.48, 1, 0.82, 1)),
        )
        for label, cy, fill, rim in buttons:
            bx, by = self.x + w * 0.18, self.y + h * (cy - 0.043)
            bw, bh = w * 0.64, h * 0.086
            Color(0, 0, 0, 0.24)
            RoundedRectangle(pos=(bx, by - 4), size=(bw, bh), radius=[bh * 0.5])
            Color(*fill)
            RoundedRectangle(pos=(bx, by), size=(bw, bh), radius=[bh * 0.5])
            Color(*rim)
            Line(rounded_rectangle=(bx, by, bw, bh, bh * 0.5), width=1.7)
            Color(1, 1, 1, 0.20)
            Line(points=[bx + 24, by + bh - 9, bx + bw - 24, by + bh - 9], width=1.5)
            self.draw_centered_canvas_text(label, self.x + w * 0.5,
                                           self.y + h * cy, max(16, w * 0.040),
                                           (1, 1, 1, 1),
                                           max_width=bw * 0.88, max_height=bh * 0.68)
        self.draw_centered_canvas_text("TAP A BUTTON TO BEGIN",
                                       self.x + w * 0.5, self.y + h * 0.145,
                                       max(10, w * 0.024), (0.60, 0.83, 1, 1))

    def draw_menu_panel(self, w, h, heading, subtitle):
        panel_w, panel_h = w * 0.84, h * 0.72
        panel_x, panel_y = self.x + (w - panel_w) / 2, self.y + h * 0.10
        Color(0.18, 0.55, 1, 0.18)
        RoundedRectangle(pos=(panel_x - 6, panel_y - 6),
                         size=(panel_w + 12, panel_h + 12), radius=[36])
        Color(0.018, 0.035, 0.105, 0.90)
        RoundedRectangle(pos=(panel_x, panel_y), size=(panel_w, panel_h), radius=[32])
        Color(0.34, 0.80, 1, 0.95)
        Line(rounded_rectangle=(panel_x, panel_y, panel_w, panel_h, 32), width=1.8)
        self.draw_centered_canvas_text(heading, self.x + w * 0.5,
                                       self.y + h * 0.80, max(29, w * 0.070),
                                       (1.0, 0.94, 0.58, 1),
                                       max_width=panel_w * 0.88, max_height=h * 0.075)
        self.draw_centered_canvas_text(subtitle, self.x + w * 0.5,
                                       self.y + h * 0.70, max(11, w * 0.028),
                                       (0.55, 0.90, 1, 1),
                                       max_width=panel_w * 0.88, max_height=h * 0.045)

    def draw_settings_menu(self, w, h):
        self.draw_menu_panel(w, h, "SETTINGS", "PICK YOUR ADVENTURE STYLE")
        colors = {
            "EASY": (0.08, 0.62, 0.48, 1),
            "NORMAL": (0.10, 0.52, 0.90, 1),
            "HARD": (0.72, 0.25, 0.55, 1)
        }
        for label, cy in (("EASY", 0.46), ("NORMAL", 0.36), ("HARD", 0.26)):
            selected = label.title() == self.difficulty
            bx, by, bw, bh = self.x + w * 0.18, self.y + h * (cy - 0.043), w * 0.64, h * 0.086
            Color(0, 0, 0, 0.22)
            RoundedRectangle(pos=(bx, by - 3), size=(bw, bh), radius=[bh * 0.5])
            if selected:
                Color(*colors[label])
            else:
                Color(0.07, 0.16, 0.32, 0.98)
            RoundedRectangle(pos=(bx, by), size=(bw, bh), radius=[bh * 0.5])
            Color(0.48, 0.88, 1, 0.9)
            Line(rounded_rectangle=(bx, by, bw, bh, bh * 0.5), width=1.5)
            self.draw_centered_canvas_text(("✓  " if selected else "✦  ") + label,
                                           self.x + w * 0.5, self.y + h * cy,
                                           max(16, w * 0.040), (1, 1, 1, 1),
                                           max_width=bw * 0.88, max_height=bh * 0.68)
        self.draw_centered_canvas_text("←  BACK TO MENU", self.x + w * 0.5,
                                       self.y + h * 0.15, max(14, w * 0.033),
                                       (0.70, 0.91, 1, 1))

    def draw_help_menu(self, w, h):
        self.draw_menu_panel(w, h, "HOW TO PLAY", "FIVE LITTLE TIPS FOR YOUR RUN")
        instructions = (
            "☝  DRAG TO STEER YOUR SHIP",
            "☄  DODGE METEORS & ENEMY FIRE",
            "★  COLLECT STARS & POWER-UPS",
            "👾  BOSS BATTLES EVERY 5 LEVELS",
            "♥  YOU HAVE 3 LIVES",
        )
        for index, line in enumerate(instructions):
            cy = 0.565 - index * 0.078
            bx, by, bw, bh = self.x + w * 0.13, self.y + h * (cy - 0.027), w * 0.74, h * 0.054
            Color(0.12, 0.54, 1, 0.16)
            RoundedRectangle(pos=(bx, by), size=(bw, bh), radius=[bh * 0.5])
            Color(0.34, 0.78, 1, 0.52)
            Line(rounded_rectangle=(bx, by, bw, bh, bh * 0.5), width=1)
            self.draw_centered_canvas_text(line, self.x + w * 0.5,
                                           self.y + h * cy, max(11, w * 0.028),
                                           (0.91, 0.97, 1, 1),
                                           max_width=bw * 0.90, max_height=bh * 0.68)
        self.draw_centered_canvas_text("←  BACK TO MENU", self.x + w * 0.5,
                                       self.y + h * 0.15, max(14, w * 0.033),
                                       (0.70, 0.91, 1, 1))

    def redraw(self, *args):
        self.canvas.clear()
        w, h = self.width, self.height
        if w <= 0 or h <= 0:
            return
        # Each level cycles through a distinct space environment palette.
        themes = [
            ((0.012, 0.018, 0.065, 1), (0.035, 0.09, 0.19, 0.28), (0.12, 0.035, 0.20, 0.20), (0.58, 0.80, 1, 0.75)),
            ((0.075, 0.012, 0.035, 1), (0.30, 0.045, 0.055, 0.30), (0.22, 0.025, 0.10, 0.24), (1, 0.42, 0.30, 0.85)),
            ((0.008, 0.045, 0.085, 1), (0.025, 0.20, 0.30, 0.30), (0.025, 0.10, 0.22, 0.24), (0.35, 0.88, 1, 0.85)),
            ((0.035, 0.008, 0.075, 1), (0.16, 0.035, 0.30, 0.32), (0.28, 0.025, 0.24, 0.22), (0.82, 0.52, 1, 0.85)),
            ((0.008, 0.055, 0.035, 1), (0.025, 0.22, 0.12, 0.30), (0.08, 0.18, 0.045, 0.24), (0.48, 1, 0.65, 0.85)),
        ]
        travel_progress = 0.0
        if self.screen == "game" and self.transition_time > 0:
            raw_progress = 1.0 - self.transition_time / self.transition_duration
            travel_progress = raw_progress * raw_progress * (3.0 - 2.0 * raw_progress)
        scene_level = max(1, self.level - 1) if self.transition_time > 0 else max(1, self.level)
        bg, glow_a, glow_b, star_tint = themes[(scene_level - 1) % len(themes)]
        with self.canvas:
            # Current sector moves down and out of view as the ship climbs.
            PushMatrix()
            Translate(0, -h * travel_progress, 0)
            Color(*bg)
            Rectangle(pos=self.pos, size=self.size)
            Color(*glow_a)
            Ellipse(pos=(self.x + w * 0.06, self.y + h * 0.48), size=(w * 0.9, h * 0.48))
            Color(*glow_b)
            Ellipse(pos=(self.x + w * 0.32, self.y + h * 0.1), size=(w * 0.8, h * 0.42))
            # Layered nebula clouds: overlapping soft color fields make each sector feel deeper.
            nebula_shift = (scene_level - 1) % 5
            nebula_x = self.x + w * (0.12 + nebula_shift * 0.13)
            Color(star_tint[0], star_tint[1], star_tint[2], 0.10)
            Ellipse(pos=(nebula_x - w * 0.22, self.y + h * 0.43), size=(w * 0.62, h * 0.20))
            Color(glow_b[0], glow_b[1], glow_b[2], 0.16)
            Ellipse(pos=(nebula_x + w * 0.05, self.y + h * 0.30), size=(w * 0.58, h * 0.18))
            Color(glow_a[0], glow_a[1], glow_a[2], 0.13)
            Ellipse(pos=(nebula_x - w * 0.30, self.y + h * 0.62), size=(w * 0.55, h * 0.13))

            # Retro pixel-art starfield: crisp square stars and occasional plus-shaped glints.
            pixel_colors = [
                (0.16, 0.35, 1.0, 0.95), (0.55, 0.12, 1.0, 0.9),
                (0.05, 0.85, 1.0, 0.9), (0.92, 0.30, 1.0, 0.85),
                (0.25, 0.95, 0.75, 0.85)
            ]
            for index, (sx, sy, radius) in enumerate(self.background_stars):
                tint = pixel_colors[index % len(pixel_colors)]
                px = self.x + sx * w
                drift = self.background_drift * (0.35 + (index % 5) * 0.12)
                py = self.y + ((sy - drift) % 1.0) * h
                pixel = max(2, radius * 2.0)
                Color(*tint)
                Rectangle(pos=(px, py), size=(pixel, pixel))
                if index % 17 == 0:
                    Rectangle(pos=(px - 1, py - 5), size=(pixel + 2, 12))
                    Rectangle(pos=(px - 5, py - 1), size=(12, pixel + 2))

            # Large pixel-space planets with neon halos and ring details.
            planet_x = self.x + w * (0.72 if scene_level % 2 else 0.24)
            planet_y = self.y + h * (0.79 if scene_level % 3 else 0.67)
            planet_r = min(w, h) * 0.105
            planet_colors = [
                (0.05, 0.78, 0.72, 1), (0.40, 0.20, 0.95, 1),
                (0.95, 0.25, 0.72, 1), (0.12, 0.48, 1, 1),
                (0.28, 0.82, 0.95, 1)
            ]
            planet_color = planet_colors[(scene_level - 1) % len(planet_colors)]
            Color(0.18, 0.10, 1, 0.18)
            Ellipse(pos=(planet_x - planet_r * 1.65, planet_y - planet_r * 1.65),
                    size=(planet_r * 3.3, planet_r * 3.3))
            Color(0.12, 0.20, 0.95, 0.75)
            Line(ellipse=(planet_x - planet_r * 1.55, planet_y - planet_r * 0.52,
                          planet_r * 3.1, planet_r * 1.05), width=2.0)
            Color(*planet_color)
            Ellipse(pos=(planet_x - planet_r, planet_y - planet_r),
                    size=(planet_r * 2, planet_r * 2))
            Color(0.02, 0.10, 0.45, 0.28)
            for band in range(4):
                Rectangle(pos=(planet_x - planet_r * 0.78,
                               planet_y - planet_r * 0.55 + band * planet_r * 0.34),
                          size=(planet_r * (1.2 + (band % 2) * 0.25), planet_r * 0.12))
            # Surface highlights, shadow edge and tiny crater details.
            Color(0.72, 0.98, 1, 0.22)
            Ellipse(pos=(planet_x - planet_r * 0.66, planet_y + planet_r * 0.22),
                    size=(planet_r * 0.72, planet_r * 0.30))
            Color(0.005, 0.025, 0.16, 0.28)
            Ellipse(pos=(planet_x + planet_r * 0.28, planet_y - planet_r * 0.68),
                    size=(planet_r * 0.52, planet_r * 1.32))
            Color(0.01, 0.16, 0.36, 0.34)
            for crater_x, crater_y, crater_size in ((-0.38, 0.12, 0.13), (0.34, 0.28, 0.09), (-0.12, -0.35, 0.08)):
                Ellipse(pos=(planet_x + planet_r * crater_x - planet_r * crater_size,
                            planet_y + planet_r * crater_y - planet_r * crater_size),
                        size=(planet_r * crater_size * 2, planet_r * crater_size * 2))

            # A second, smaller moon and a distant ringed planet create a real multi-world scene.
            moon_x = self.x + w * (0.18 if scene_level % 2 else 0.82)
            moon_y = self.y + h * (0.56 if scene_level % 3 else 0.39)
            moon_r = min(w, h) * 0.037
            Color(0.55, 0.72, 1, 0.12)
            Ellipse(pos=(moon_x - moon_r * 1.5, moon_y - moon_r * 1.5), size=(moon_r * 3, moon_r * 3))
            Color(0.42, 0.58, 0.78, 1)
            Ellipse(pos=(moon_x - moon_r, moon_y - moon_r), size=(moon_r * 2, moon_r * 2))
            Color(0.10, 0.20, 0.36, 0.55)
            for crater_dx, crater_dy, crater_scale in ((-0.3, 0.2, 0.18), (0.28, -0.2, 0.13), (0.05, 0.34, 0.10)):
                Ellipse(pos=(moon_x + moon_r * crater_dx - moon_r * crater_scale,
                             moon_y + moon_r * crater_dy - moon_r * crater_scale),
                        size=(moon_r * crater_scale * 2, moon_r * crater_scale * 2))

            far_x = self.x + w * (0.84 if scene_level % 2 else 0.16)
            far_y = self.y + h * 0.30
            far_r = min(w, h) * 0.020
            Color(0.35, 0.72, 1, 0.72)
            Ellipse(pos=(far_x - far_r, far_y - far_r), size=(far_r * 2, far_r * 2))
            Color(0.65, 0.90, 1, 0.45)
            Line(ellipse=(far_x - far_r * 1.9, far_y - far_r * 0.45,
                          far_r * 3.8, far_r * 0.9), width=1.3)
            PopMatrix()

            # The next sector enters from above and scrolls down into place.
            if self.screen == "game" and self.transition_time > 0:
                next_level = max(1, self.level)
                next_bg, next_glow_a, next_glow_b, next_star_tint = themes[(next_level - 1) % len(themes)]
                PushMatrix()
                Translate(0, h * (1.0 - travel_progress), 0)
                Color(*next_bg)
                Rectangle(pos=self.pos, size=self.size)
                Color(*next_glow_a)
                Ellipse(pos=(self.x + w * 0.06, self.y + h * 0.48), size=(w * 0.9, h * 0.48))
                Color(*next_glow_b)
                Ellipse(pos=(self.x + w * 0.32, self.y + h * 0.1), size=(w * 0.8, h * 0.42))
                # Layered nebula clouds: overlapping soft color fields make each sector feel deeper.
                nebula_shift = (next_level - 1) % 5
                nebula_x = self.x + w * (0.12 + nebula_shift * 0.13)
                Color(next_star_tint[0], next_star_tint[1], next_star_tint[2], 0.10)
                Ellipse(pos=(nebula_x - w * 0.22, self.y + h * 0.43), size=(w * 0.62, h * 0.20))
                Color(next_glow_b[0], next_glow_b[1], next_glow_b[2], 0.16)
                Ellipse(pos=(nebula_x + w * 0.05, self.y + h * 0.30), size=(w * 0.58, h * 0.18))
                Color(next_glow_a[0], next_glow_a[1], next_glow_a[2], 0.13)
                Ellipse(pos=(nebula_x - w * 0.30, self.y + h * 0.62), size=(w * 0.55, h * 0.13))
    
                # Retro pixel-art starfield: crisp square stars and occasional plus-shaped glints.
                pixel_colors = [
                    (0.16, 0.35, 1.0, 0.95), (0.55, 0.12, 1.0, 0.9),
                    (0.05, 0.85, 1.0, 0.9), (0.92, 0.30, 1.0, 0.85),
                    (0.25, 0.95, 0.75, 0.85)
                ]
                for index, (sx, sy, radius) in enumerate(self.background_stars):
                    tint = pixel_colors[index % len(pixel_colors)]
                    px = self.x + sx * w
                    drift = self.background_drift * (0.35 + (index % 5) * 0.12)
                    py = self.y + ((sy - drift) % 1.0) * h
                    pixel = max(2, radius * 2.0)
                    Color(*tint)
                    Rectangle(pos=(px, py), size=(pixel, pixel))
                    if index % 17 == 0:
                        Rectangle(pos=(px - 1, py - 5), size=(pixel + 2, 12))
                        Rectangle(pos=(px - 5, py - 1), size=(12, pixel + 2))
    
                # Large pixel-space planets with neon halos and ring details.
                planet_x = self.x + w * (0.72 if next_level % 2 else 0.24)
                planet_y = self.y + h * (0.79 if next_level % 3 else 0.67)
                planet_r = min(w, h) * 0.105
                planet_colors = [
                    (0.05, 0.78, 0.72, 1), (0.40, 0.20, 0.95, 1),
                    (0.95, 0.25, 0.72, 1), (0.12, 0.48, 1, 1),
                    (0.28, 0.82, 0.95, 1)
                ]
                planet_color = planet_colors[(next_level - 1) % len(planet_colors)]
                Color(0.18, 0.10, 1, 0.18)
                Ellipse(pos=(planet_x - planet_r * 1.65, planet_y - planet_r * 1.65),
                        size=(planet_r * 3.3, planet_r * 3.3))
                Color(0.12, 0.20, 0.95, 0.75)
                Line(ellipse=(planet_x - planet_r * 1.55, planet_y - planet_r * 0.52,
                              planet_r * 3.1, planet_r * 1.05), width=2.0)
                Color(*planet_color)
                Ellipse(pos=(planet_x - planet_r, planet_y - planet_r),
                        size=(planet_r * 2, planet_r * 2))
                Color(0.02, 0.10, 0.45, 0.28)
                for band in range(4):
                    Rectangle(pos=(planet_x - planet_r * 0.78,
                                   planet_y - planet_r * 0.55 + band * planet_r * 0.34),
                              size=(planet_r * (1.2 + (band % 2) * 0.25), planet_r * 0.12))
                # Surface highlights, shadow edge and tiny crater details.
                Color(0.72, 0.98, 1, 0.22)
                Ellipse(pos=(planet_x - planet_r * 0.66, planet_y + planet_r * 0.22),
                        size=(planet_r * 0.72, planet_r * 0.30))
                Color(0.005, 0.025, 0.16, 0.28)
                Ellipse(pos=(planet_x + planet_r * 0.28, planet_y - planet_r * 0.68),
                        size=(planet_r * 0.52, planet_r * 1.32))
                Color(0.01, 0.16, 0.36, 0.34)
                for crater_x, crater_y, crater_size in ((-0.38, 0.12, 0.13), (0.34, 0.28, 0.09), (-0.12, -0.35, 0.08)):
                    Ellipse(pos=(planet_x + planet_r * crater_x - planet_r * crater_size,
                                planet_y + planet_r * crater_y - planet_r * crater_size),
                            size=(planet_r * crater_size * 2, planet_r * crater_size * 2))
    
                # A second, smaller moon and a distant ringed planet create a real multi-world scene.
                moon_x = self.x + w * (0.18 if next_level % 2 else 0.82)
                moon_y = self.y + h * (0.56 if next_level % 3 else 0.39)
                moon_r = min(w, h) * 0.037
                Color(0.55, 0.72, 1, 0.12)
                Ellipse(pos=(moon_x - moon_r * 1.5, moon_y - moon_r * 1.5), size=(moon_r * 3, moon_r * 3))
                Color(0.42, 0.58, 0.78, 1)
                Ellipse(pos=(moon_x - moon_r, moon_y - moon_r), size=(moon_r * 2, moon_r * 2))
                Color(0.10, 0.20, 0.36, 0.55)
                for crater_dx, crater_dy, crater_scale in ((-0.3, 0.2, 0.18), (0.28, -0.2, 0.13), (0.05, 0.34, 0.10)):
                    Ellipse(pos=(moon_x + moon_r * crater_dx - moon_r * crater_scale,
                                 moon_y + moon_r * crater_dy - moon_r * crater_scale),
                            size=(moon_r * crater_scale * 2, moon_r * crater_scale * 2))
    
                far_x = self.x + w * (0.84 if next_level % 2 else 0.16)
                far_y = self.y + h * 0.30
                far_r = min(w, h) * 0.020
                Color(0.35, 0.72, 1, 0.72)
                Ellipse(pos=(far_x - far_r, far_y - far_r), size=(far_r * 2, far_r * 2))
                Color(0.65, 0.90, 1, 0.45)
                Line(ellipse=(far_x - far_r * 1.9, far_y - far_r * 0.45,
                              far_r * 3.8, far_r * 0.9), width=1.3)
                PopMatrix()
            if self.screen in ("home", "settings", "over", "paused"):
                cx, cy = self.x + w * 0.5, self.y + h * 0.27
                Color(0.10, 0.72, 1, 0.18)
                Line(circle=(cx, cy, min(w, h) * 0.16), width=1.2)
                Color(0.18, 0.82, 1, 0.1)
                Line(circle=(cx, cy, min(w, h) * 0.21), width=1)
                Color(0.35, 0.92, 1, 1)
                Triangle(points=[cx, cy + 39, cx - 25, cy - 25, cx + 25, cy - 25])
                Color(1, 0.42, 0.12, 0.85)
                Ellipse(pos=(cx - 7, cy - 43), size=(14, 23))

            if self.screen == "game":
                px, py = self.x + self.player_x * w, self.y + self.player_y * h
                Color(0.05, 0.65, 1, 0.2)
                Ellipse(pos=(px - 34, py - 22), size=(68, 68))
                # Layered, flickering engine plume behind the ship.
                flame = 20 + 7 * (0.5 + 0.5 * math.sin(self.level_time * 28))
                Color(1, 0.22, 0.035, 0.30)
                Triangle(points=[px, py - flame - 13, px - 15, py - 15, px + 15, py - 15])
                Color(1, 0.38, 0.06, 0.95)
                Triangle(points=[px, py - flame, px - 9, py - 14, px + 9, py - 14])
                Color(0.35, 0.92, 1, 0.95)
                Triangle(points=[px, py - flame * 0.65, px - 4, py - 15, px + 4, py - 15])
                # Detailed player craft: swept wings, armored fuselage, cockpit,
                # engine nacelles, panel seams and bright metallic edge highlights.
                Color(0.015, 0.16, 0.34, 1)
                Triangle(points=[px - 2, py + 13, px - 34, py - 15, px - 18, py - 23])
                Triangle(points=[px + 2, py + 13, px + 34, py - 15, px + 18, py - 23])
                Color(0.08, 0.42, 0.72, 1)
                Triangle(points=[px, py + 35, px - 28, py - 19, px + 28, py - 19])
                Color(0.35, 0.88, 1, 1)
                Triangle(points=[px, py + 34, px - 8, py - 17, px + 8, py - 17])
                Color(0.72, 0.94, 1, 1)
                Line(points=[px, py + 30, px - 21, py - 13, px - 30, py - 17], width=1.5)
                Line(points=[px, py + 30, px + 21, py - 13, px + 30, py - 17], width=1.5)
                # Extra luminous wing inlays and animated engine glow add depth.
                wing_pulse = 0.55 + 0.45 * math.sin(self.level_time * 9)
                Color(0.12, 0.88, 1, 0.75 * wing_pulse)
                Line(points=[px - 25, py - 12, px - 13, py - 5, px - 7, py + 7], width=2)
                Line(points=[px + 25, py - 12, px + 13, py - 5, px + 7, py + 7], width=2)
                Color(0.10, 0.72, 1, 0.22 * wing_pulse)
                Ellipse(pos=(px - 34, py - 23), size=(13, 10))
                Ellipse(pos=(px + 21, py - 23), size=(13, 10))
                Color(0.72, 0.96, 1, 0.95)
                Line(points=[px - 3, py + 12, px, py + 24, px + 3, py + 12], width=1.4)
                Color(0.015, 0.07, 0.16, 1)
                Triangle(points=[px, py + 23, px - 7, py + 1, px + 7, py + 1])
                Color(0.25, 0.9, 1, 1)
                Ellipse(pos=(px - 5, py + 5), size=(10, 17))
                Color(0.88, 0.98, 1, 0.9)
                Line(points=[px, py + 18, px, py + 7], width=1.2)
                Color(0.04, 0.24, 0.42, 1)
                Rectangle(pos=(px - 25, py - 17), size=(8, 4))
                Rectangle(pos=(px + 17, py - 17), size=(8, 4))
                Color(0.35, 0.92, 1, 1)
                Ellipse(pos=(px - 27, py - 19), size=(5, 5))
                Ellipse(pos=(px + 22, py - 19), size=(5, 5))
                Color(1, 0.42, 0.12, 0.95)
                Triangle(points=[px, py - 42, px - 8, py - 18, px + 8, py - 18])

                for enemy in self.enemies:
                    ex, ey = self.x + enemy[0] * w, self.y + enemy[1] * h
                    enemy_type = int(enemy[6])
                    enemy_colors = ((1.0, 0.28, 0.32), (1.0, 0.62, 0.16), (0.72, 0.32, 1.0))
                    tint = enemy_colors[enemy_type]
                    pulse = 0.65 + 0.35 * math.sin(enemy[4] * 7)
                    # Compact hostile fighter with swept wings, cockpit and engine glow.
                    Color(tint[0], tint[1], tint[2], 0.18)
                    Ellipse(pos=(ex - 30, ey - 25), size=(60, 50))
                    Color(0.055, 0.075, 0.16, 1)
                    Triangle(points=[ex, ey - 24, ex - 29, ey + 13, ex - 10, ey + 8])
                    Triangle(points=[ex, ey - 24, ex + 29, ey + 13, ex + 10, ey + 8])
                    Color(*tint, 1)
                    Triangle(points=[ex, ey - 27, ex - 17, ey + 20, ex + 17, ey + 20])
                    Color(min(1, tint[0] * 1.25), min(1, tint[1] * 1.25), min(1, tint[2] * 1.25), 1)
                    Triangle(points=[ex, ey - 17, ex - 7, ey + 14, ex + 7, ey + 14])
                    Color(0.04, 0.12, 0.22, 1)
                    Ellipse(pos=(ex - 5, ey + 2), size=(10, 13))
                    Color(0.75, 0.94, 1, pulse)
                    Ellipse(pos=(ex - 3, ey + 5), size=(6, 7))
                    Color(1.0, 0.30, 0.12, pulse)
                    for engine_x in (-12, 12):
                        Ellipse(pos=(ex + engine_x - 3, ey + 14), size=(6, 9))
                    # Small health pips show tougher fighters need extra hits.
                    for pip in range(enemy[3]):
                        Color(0.12, 0.95, 0.72, 0.9 if pip < enemy[2] else 0.18)
                        Ellipse(pos=(ex - enemy[3] * 4 + pip * 8, ey + 27), size=(5, 5))

                for sx, sy, vx, vy in self.enemy_shots:
                    x, y = self.x + sx * w, self.y + sy * h
                    Color(1.0, 0.28, 0.32, 0.18)
                    Ellipse(pos=(x - 12, y - 12), size=(24, 24))
                    Color(1.0, 0.30, 0.22, 1)
                    Ellipse(pos=(x - 6, y - 6), size=(12, 12))
                    Color(1.0, 0.88, 0.72, 1)
                    Ellipse(pos=(x - 2.5, y - 2.5), size=(5, 5))

                for shot in self.boss_shots:
                    sx, sy, vx, vy = shot[:4]
                    x, y = self.x + sx * w, self.y + sy * h
                    shot_tint = (1.0, 0.18, 0.34, 1) if vx < -0.04 else (
                        (1.0, 0.48, 0.12, 1) if vx > 0.04 else (0.42, 0.72, 1.0, 1))
                    # Draw a fading, tapered plasma wake using the projectile's
                    # actual recent positions. Older trail segments become softer.
                    trail = shot[4] if len(shot) > 4 else []
                    trail_points = [(self.x + p[0] * w, self.y + p[1] * h, p[2])
                                    for p in trail]
                    for index in range(1, len(trail_points)):
                        ax, ay, age_alpha = trail_points[index - 1]
                        bx, by, fresh_alpha = trail_points[index]
                        alpha = min(age_alpha, fresh_alpha)
                        width = 2.0 + 7.0 * alpha
                        Color(shot_tint[0], shot_tint[1], shot_tint[2], 0.10 + 0.30 * alpha)
                        Line(points=[ax, ay, bx, by], width=width * 2.2)
                        Color(shot_tint[0], shot_tint[1], shot_tint[2], 0.20 + 0.58 * alpha)
                        Line(points=[ax, ay, bx, by], width=width)
                        Color(1.0, 0.84, 0.78, 0.20 + 0.35 * alpha)
                        Line(points=[ax, ay, bx, by], width=max(1, width * 0.28))
                    # Bright exhaust plume and layered plasma shell/core.
                    direction_len = max(0.0001, math.hypot(vx, vy))
                    back_x = -vx / direction_len
                    back_y = -vy / direction_len
                    plume_len = min(w, h) * 0.030
                    Color(shot_tint[0], shot_tint[1], shot_tint[2], 0.28)
                    Ellipse(pos=(x + back_x * plume_len - 7,
                                 y + back_y * plume_len - 7), size=(14, 14))
                    Color(shot_tint[0], shot_tint[1], shot_tint[2], 0.24)
                    Ellipse(pos=(x - 17, y - 17), size=(34, 34))
                    Color(shot_tint[0], shot_tint[1], shot_tint[2], 0.98)
                    Ellipse(pos=(x - 9, y - 9), size=(18, 18))
                    Color(1.0, 0.66, 0.56, 1)
                    Ellipse(pos=(x - 5, y - 5), size=(10, 10))
                    Color(1, 1, 1, 1)
                    Ellipse(pos=(x - 2.2, y - 2.2), size=(4.4, 4.4))

                if self.boss is not None:
                    bx, by, hp, max_hp, phase, attack = self.boss[:6]
                    boss_type = int(self.boss[6]) % 5 if len(self.boss) > 6 else 0
                    boss_glows = ((0.05, 0.72, 1.0), (1.0, 0.42, 0.12),
                                  (0.92, 0.30, 0.12), (0.66, 0.24, 1.0),
                                  (0.20, 1.0, 0.72))
                    boss_glow = boss_glows[boss_type]
                    x, y = self.x + bx * w, self.y + by * h
                    radius = min(w, h) * (0.105 if boss_type != 2 else 0.12)
                    pulse = 0.5 + 0.5 * math.sin(phase * 3.2)
                    # Each boss gets its own energy color and silhouette accents.
                    Color(boss_glow[0], boss_glow[1], boss_glow[2], 0.13 + pulse * 0.10)
                    Ellipse(pos=(x - radius * 1.72, y - radius * 1.42),
                            size=(radius * 3.44, radius * 2.84))
                    Color(0.035, 0.10, 0.24, 1)
                    Triangle(points=[x - radius * 0.35, y + radius * 0.35,
                                     x - radius * 1.65, y - radius * 0.38,
                                     x - radius * 1.12, y - radius * 0.92])
                    Triangle(points=[x + radius * 0.35, y + radius * 0.35,
                                     x + radius * 1.65, y - radius * 0.38,
                                     x + radius * 1.12, y - radius * 0.92])
                    Color(*(boss_glow + (1,)))
                    Triangle(points=[x, y + radius * 1.18,
                                     x - radius * 1.28, y - radius * 0.48,
                                     x + radius * 1.28, y - radius * 0.48])
                    Color(min(1, boss_glow[0] * 1.25), min(1, boss_glow[1] * 1.25), min(1, boss_glow[2] * 1.25), 1)
                    Triangle(points=[x, y + radius * 0.96,
                                     x - radius * 0.78, y - radius * 0.42,
                                     x + radius * 0.78, y - radius * 0.42])
                    # Metallic edge lines and segmented armor plating.
                    Color(0.55, 0.88, 1, 0.95)
                    Line(points=[x, y + radius * 1.08,
                                 x - radius * 1.45, y - radius * 0.42], width=1.8)
                    Line(points=[x, y + radius * 1.08,
                                 x + radius * 1.45, y - radius * 0.42], width=1.8)
                    Color(0.015, 0.045, 0.12, 1)
                    Triangle(points=[x, y + radius * 0.62,
                                     x - radius * 0.40, y - radius * 0.42,
                                     x + radius * 0.40, y - radius * 0.42])
                    # Bright central energy reactor with a breathing halo.
                    Color(boss_glow[0], boss_glow[1], boss_glow[2], 0.20 + pulse * 0.18)
                    Ellipse(pos=(x - radius * 0.52, y - radius * 0.38),
                            size=(radius * 1.04, radius * 1.04))
                    Color(*boss_glow, 1)
                    Ellipse(pos=(x - radius * 0.29, y - radius * 0.18),
                            size=(radius * 0.58, radius * 0.58))
                    Color(0.82, 0.98, 1, 1)
                    Ellipse(pos=(x - radius * 0.13, y - radius * 0.02),
                            size=(radius * 0.26, radius * 0.26))
                    # Twin luminous visor panels and small status lights.
                    Color(1, 0.28, 0.36, 1)
                    Line(points=[x - radius * 0.58, y + radius * 0.28,
                                 x - radius * 0.16, y + radius * 0.18], width=2.4)
                    Line(points=[x + radius * 0.58, y + radius * 0.28,
                                 x + radius * 0.16, y + radius * 0.18], width=2.4)
                    Color(0.25, 0.94, 1, 1)
                    for light_offset in (-1.05, -0.82, 0.82, 1.05):
                        Ellipse(pos=(x + radius * light_offset - 2,
                                     y - radius * 0.48), size=(4, 4))
                    # A rotating-looking energy shield ring, purely visual.
                    Color(boss_glow[0], boss_glow[1], boss_glow[2], 0.34 + pulse * 0.22)
                    Line(ellipse=(x - radius * 1.52, y - radius * 0.72,
                                  radius * 3.04, radius * 1.52), width=1.4)
                    Color(0.9, 0.98, 1, 0.8)
                    Line(points=[x - radius * 1.34, y - radius * 0.65,
                                 x - radius * 1.05, y - radius * 0.78], width=2)
                    Line(points=[x + radius * 1.34, y - radius * 0.65,
                                 x + radius * 1.05, y - radius * 0.78], width=2)
                    # Distinct physical features make each boss recognizable.
                    if boss_type == 1:
                        Color(1.0, 0.58, 0.16, 1)
                        for side in (-1, 1):
                            Ellipse(pos=(x + side * radius * 1.18 - radius * 0.22,
                                         y - radius * 0.20), size=(radius * 0.44, radius * 0.44))
                    elif boss_type == 2:
                        Color(0.98, 0.42, 0.16, 1)
                        for side in (-1, 1):
                            Triangle(points=[x + side * radius * 0.55, y + radius * 0.55,
                                             x + side * radius * 1.75, y + radius * 1.15,
                                             x + side * radius * 1.18, y - radius * 0.25])
                    elif boss_type == 3:
                        Color(0.82, 0.50, 1, 0.85)
                        Line(circle=(x, y, radius * 1.78), width=3)
                        Line(circle=(x, y, radius * 1.42), width=1.5)
                    elif boss_type == 4:
                        Color(0.20, 1.0, 0.72, 1)
                        for side in (-1, 1):
                            Line(points=[x + side * radius * 0.42, y + radius * 0.75,
                                         x + side * radius * 1.85, y + radius * 1.55,
                                         x + side * radius * 1.45, y + radius * 0.15], width=3)
                    bar_w = w * 0.62
                    bar_x = self.x + (w - bar_w) * 0.5
                    bar_y = self.y + h * 0.91
                    Color(0.2, 0.08, 0.14, 0.95)
                    Rectangle(pos=(bar_x, bar_y), size=(bar_w, 9))
                    Color(boss_glow[0], boss_glow[1], boss_glow[2], 1)
                    Rectangle(pos=(bar_x, bar_y), size=(bar_w * max(0, hp) / max_hp, 9))
                    if self.boss_notice > 0:
                        Color(1, 0.25, 0.35, 1)

                for meteor in self.asteroids:
                    mx, my, scale, fall_speed = meteor[:4]
                    x, y = self.x + mx * w, self.y + my * h
                    r = 15 * scale
                    variant = meteor[4] if len(meteor) > 4 else 0
                    rotation = meteor[5] if len(meteor) > 5 else 0.0
                    # A layered hot tail makes each falling meteor readable in motion.
                    Color(1, 0.12, 0.015, 0.13)
                    Triangle(points=[x, y + r * 4.0, x - r * 1.1, y + r * 0.2, x + r * 1.1, y + r * 0.2])
                    Color(1, 0.30, 0.025, 0.42)
                    Triangle(points=[x, y + r * 3.0, x - r * 0.68, y + r * 0.15, x + r * 0.68, y + r * 0.15])
                    Color(1, 0.18, 0.02, 0.14)
                    Ellipse(pos=(x - r * 2, y - r * 1.8), size=(r * 4, r * 4))
                    Color(1, 0.22, 0.02, 0.78)
                    Triangle(points=[x, y + r * 2.8, x - r * 0.78, y + r * 0.1, x + r * 0.78, y + r * 0.1])
                    Color(1, 0.68, 0.12, 0.95)
                    Triangle(points=[x, y + r * 2.0, x - r * 0.4, y + r * 0.1, x + r * 0.4, y + r * 0.1])
                    rock_colors = ((0.48, 0.24, 0.2, 1), (0.34, 0.29, 0.27, 1),
                                   (0.52, 0.19, 0.12, 1), (0.30, 0.25, 0.42, 1))
                    rock = rock_colors[variant % len(rock_colors)]
                    Color(*rock)
                    Ellipse(pos=(x - r, y - r), size=(r * 2, r * 2))
                    # Jagged rocky rim and angular surface plates.
                    points = []
                    for corner in range(10):
                        angle = rotation + corner * math.tau / 10
                        radius = r * (0.78 + 0.20 * ((corner + variant) % 3) / 2)
                        points.extend((x + math.cos(angle) * radius, y + math.sin(angle) * radius))
                    Color(0.78, 0.48, 0.32, 0.95)
                    Line(points=points, close=True, width=1.5)
                    Color(0.95, 0.52, 0.3, 0.9)
                    Ellipse(pos=(x - r * 0.48, y + r * 0.08), size=(r * 0.42, r * 0.34))
                    Color(0.12, 0.055, 0.045, 0.72)
                    for crater_dx, crater_dy, crater_r in ((-0.35, 0.18, 0.13), (0.30, -0.25, 0.11), (0.08, 0.38, 0.08)):
                        Ellipse(pos=(x + r * crater_dx - r * crater_r,
                                     y + r * crater_dy - r * crater_r),
                                size=(r * crater_r * 2, r * crater_r * 2))
                    # Bright molten fissures give each meteor a distinct hot surface.
                    Color(1, 0.68, 0.22, 0.95)
                    Line(points=[x - r * 0.18, y + r * 0.62,
                                 x + r * 0.02, y + r * 0.18,
                                 x - r * 0.10, y - r * 0.12], width=1.6)
                    Line(points=[x + r * 0.02, y + r * 0.18,
                                 x + r * 0.48, y + r * 0.34], width=1.3)

                # Expanding neon shock rings make impacts feel punchier.
                for blast_x, blast_y, age in self.blasts:
                    radius = (0.018 + age * 0.30) * min(w, h)
                    alpha = max(0.0, 1.0 - age / 0.48)
                    bx, by = self.x + blast_x * w, self.y + blast_y * h
                    Color(1.0, 0.42, 0.10, alpha * 0.85)
                    Line(circle=(bx, by, radius), width=max(1.0, 3.0 * alpha))
                    Color(0.12, 0.78, 1.0, alpha * 0.45)
                    Line(circle=(bx, by, radius * 0.62), width=max(1.0, 2.0 * alpha))

                for x, y, vx, vy, life, particle_size in self.particles:
                    alpha = min(1.0, life * 2.2)
                    Color(1, 0.48, 0.12, alpha)
                    Ellipse(pos=(self.x + x * w - particle_size, self.y + y * h - particle_size),
                            size=(particle_size * 2, particle_size * 2))

                for star in self.stars:
                    sx, sy = star[0], star[1]
                    spin = star[2] if len(star) > 2 else 0.0
                    x, y = self.x + sx * w, self.y + sy * h
                    # Gold collectible coin: spinning metallic edge, inset face,
                    # engraved star, and a soft reflected highlight.
                    coin_w = max(0.28, abs(math.cos(spin))) * 21
                    Color(1.0, 0.62, 0.06, 0.16)
                    Ellipse(pos=(x - 19, y - 19), size=(38, 38))
                    Color(0.38, 0.19, 0.025, 1)
                    Ellipse(pos=(x - coin_w - 2, y - 13), size=(coin_w * 2 + 4, 26))
                    Color(1.0, 0.66, 0.08, 1)
                    Ellipse(pos=(x - coin_w, y - 11), size=(coin_w * 2, 22))
                    Color(1.0, 0.88, 0.34, 1)
                    Line(ellipse=(x - coin_w * 0.78, y - 8.5,
                                  coin_w * 1.56, 17), width=1.4)
                    Color(0.72, 0.37, 0.025, 1)
                    Ellipse(pos=(x - coin_w * 0.48, y - 5.5),
                            size=(coin_w * 0.96, 11))
                    Color(1.0, 0.96, 0.68, 1)
                    Line(points=[x, y + 6, x + coin_w * 0.25, y,
                                 x, y - 6, x - coin_w * 0.25, y, x, y + 6],
                         width=1.8)
                    Color(1, 1, 0.88, 0.85)
                    Line(points=[x - coin_w * 0.35, y + 7,
                                 x - coin_w * 0.12, y + 9], width=1.2)

                # Collectible power-up capsules: cyan shield, gold score, green speed.
                pickup_styles = (
                    ((0.10, 0.72, 1, 0.22), (0.18, 0.82, 1, 1)),
                    ((1, 0.68, 0.08, 0.22), (1, 0.82, 0.18, 1)),
                    ((0.12, 1, 0.48, 0.22), (0.20, 1, 0.56, 1))
                )
                for power_x, power_y, power_type in self.powerups:
                    x, y = self.x + power_x * w, self.y + power_y * h
                    glow, core = pickup_styles[power_type]
                    Color(*glow)
                    Ellipse(pos=(x - 19, y - 19), size=(38, 38))
                    Color(*core)
                    Line(circle=(x, y, 12), width=2.2)
                    if power_type == 0:
                        # Shield emblem.
                        Line(points=[x, y + 8, x + 7, y + 4, x + 6, y - 4,
                                     x, y - 9, x - 6, y - 4, x - 7, y + 4, x, y + 8], width=2)
                    elif power_type == 1:
                        self.draw_canvas_text("+", x - 6, y - 7, 17, (1, 0.91, 0.45, 1))
                    else:
                        Line(points=[x + 2, y + 9, x - 5, y - 1, x + 1, y - 1,
                                     x - 2, y - 9, x + 7, y + 2, x + 1, y + 2], width=2.2)

                if self.shield_time > 0:
                    Color(0.12, 0.82, 1, 0.30 + 0.12 * math.sin(self.level_time * 8))
                    Line(circle=(px, py, 48), width=2.8)
                    Color(0.55, 0.96, 1, 0.65)
                    Line(circle=(px, py, 42), width=1.0)

            # Larger bubble-style HUD: rounded glass capsules with soft neon glow.
            if self.screen == "game":
                panel_h = max(72, h * 0.086)
                panel_y = self.y + h * 0.842
                panel_w = w * 0.30
                panel_xs = (self.x + w * 0.025, self.x + w * 0.35, self.x + w * 0.675)
                font = max(18, min(26, w * 0.041))
                for panel_x in panel_xs:
                    # Outer glow and deep translucent rounded glass.
                    Color(0.02, 0.48, 1, 0.18)
                    RoundedRectangle(pos=(panel_x - 3, panel_y - 3),
                                     size=(panel_w + 6, panel_h + 6), radius=[24])
                    Color(0.012, 0.035, 0.105, 0.94)
                    RoundedRectangle(pos=(panel_x, panel_y),
                                     size=(panel_w, panel_h), radius=[21])
                    Color(0.12, 0.68, 1, 0.92)
                    Line(rounded_rectangle=(panel_x, panel_y, panel_w, panel_h, 21),
                         width=1.55)
                    # A subtle glossy highlight across the top of each bubble.
                    Color(0.48, 0.88, 1, 0.16)
                    Line(points=[panel_x + 20, panel_y + panel_h - 8,
                                 panel_x + panel_w - 20, panel_y + panel_h - 8],
                         width=1.3)

                # Level bubble: bold label and a small glowing indicator.
                level_cx = panel_xs[0] + panel_w * 0.5
                Color(0.18, 0.78, 1, 0.95)
                Ellipse(pos=(panel_xs[0] + 13, panel_y + panel_h * 0.43),
                        size=(9, 9))
                self.draw_canvas_text(f"LEVEL {self.level}",
                                      panel_xs[0] + 29, panel_y + panel_h * 0.28,
                                      font, (0.86, 0.98, 1, 1))

                # Three larger ship icons make remaining lives easy to read.
                life_cx = panel_xs[1] + panel_w * 0.5
                life_gap = min(31, panel_w * 0.25)
                ship_y = panel_y + panel_h * 0.53
                for life_index in range(3):
                    sx = life_cx + (life_index - 1) * life_gap
                    if life_index < self.lives:
                        Color(0.02, 0.72, 1, 0.24)
                        Ellipse(pos=(sx - 14, ship_y - 15), size=(28, 30))
                        Color(0.28, 0.91, 1, 1)
                        Triangle(points=[sx, ship_y + 14, sx - 10, ship_y - 10,
                                         sx + 10, ship_y - 10])
                        Color(0.94, 1, 1, 1)
                        Line(points=[sx, ship_y + 8, sx, ship_y - 5], width=1.5)
                    else:
                        Color(0.30, 0.43, 0.60, 0.55)
                        Line(points=[sx, ship_y + 12, sx - 10, ship_y - 10,
                                     sx + 10, ship_y - 10], close=True, width=1.3)

                # Score bubble uses a mint accent to separate it from the other stats.
                Color(0.22, 1, 0.78, 0.95)
                Ellipse(pos=(panel_xs[2] + 13, panel_y + panel_h * 0.43),
                        size=(9, 9))
                self.draw_canvas_text(f"SCORE {self.score}",
                                      panel_xs[2] + 29, panel_y + panel_h * 0.28,
                                      font, (0.70, 1, 0.91, 1))

                # No on-screen steering arrows: the whole playfield is touch-and-drag.
            Color(0.12, 0.68, 1, 0.35)
            Line(points=[self.x, self.y + 1, self.x + w, self.y + 1], width=1)

            if self.screen == "home":
                self.draw_home_menu(w, h)
            elif self.screen == "settings":
                self.draw_settings_menu(w, h)
            elif self.screen == "help":
                self.draw_help_menu(w, h)
            elif self.screen == "over":
                self.draw_game_over(w, h)


class StarDodgerApp(App):
    def build(self):
        self.title = "Star Dodger 2.0"
        self.game = StarDodger()
        return self.game

    def on_start(self):
        # Re-assert the home screen after Android/Kivy has finished attaching
        # the root widget. This prevents startup from landing in gameplay.
        Clock.schedule_once(lambda dt: self.game.show_home(), 0.25)


if __name__ == "__main__":
    StarDodgerApp().run()