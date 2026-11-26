import math
from random import randint, uniform

from kivy.app import App
from kivy.core.text import Label as CoreLabel
from kivy.clock import Clock
from kivy.graphics import Color, Ellipse, Line, Rectangle, Triangle, PushMatrix, PopMatrix, Translate
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
        self.hint.text = "TOUCH AND DRAG ANYWHERE TO STEER"
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
        self.best_score = max(self.best_score, self.score)
        self.title.text = "[b]GAME[/b] [color=ff657a]OVER[/color]"
        self.title.markup = True
        self.subtitle.text = "RUN COMPLETE"
        self.info.pos_hint = {"center_x": 0.5, "center_y": 0.55}
        self.info.height = 112
        self.info.font_size = "20sp"
        self.info.text = (
            f"[b]FINAL SCORE  {self.score}[/b]\n"
            f"LEVEL REACHED  {self.level}\n"
            f"BEST SCORE  {self.best_score}"
        )
        self.info.markup = True
        self.hint.text = "TRY AGAIN AND REACH THE NEXT SECTOR"
        for widget in (self.title, self.subtitle, self.info, self.hint):
            self.set_visible(widget, True)
        for hud in (self.hud_level, self.hud_lives, self.hud_score):
            self.set_visible(hud, False)
        self.set_visible(self.retry_button, True)
        self.set_visible(self.home_button, True)
        self.set_visible(self.play_button, False)
        self.set_visible(self.settings_button, False)
        self.hide_game_controls()
        self.redraw()

    def shift_player(self, amount):
        if self.screen == "game":
            # Arrow taps set a destination; glide toward it instead of teleporting.
            self.player_target_x = max(0.07, min(0.93, self.player_target_x + amount))

    def move_player_to(self, x):
        if self.width > 0:
            self.player_x = max(0.06, min(0.94, (x - self.x) / self.width))
            self.player_target_x = self.player_x
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
            self.move_player_to(touch.x)
            touch.grab(self)
            return True
        return False

    def on_touch_move(self, touch):
        if self.screen == "game" and touch.grab_current is self:
            self.move_player_to(touch.x)
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

    def update(self, dt):
        if not self.game_started or self.screen != "game":
            return False
        dt = min(dt, 0.05)
        self.level_time += dt
        self.score_time += dt
        self.background_drift = (self.background_drift + dt * 0.018) % 1.0
        self.transition_time = max(0.0, self.transition_time - dt)
        # Smooth, frame-rate-independent movement follows the player's finger.
        slide_rate = 13.0 if self.speed_boost_time > 0 else 8.0
        slide_factor = 1.0 - math.exp(-dt * slide_rate)
        self.player_x += (self.player_target_x - self.player_x) * slide_factor
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
                boss_hp = 12 + (self.level // 5 - 1) * 5
                self.boss = [0.5, 0.80, boss_hp, boss_hp, 0.0, 0.0]
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
            self.stars.append([uniform(0.06, 0.94), 1.06])

        self.shot_time += dt
        if self.shot_time >= 0.42:
            self.shot_time = 0.0
            self.bullets.append([self.player_x, 0.22])

        for bullet in self.bullets[:]:
            bullet[1] += dt * 1.05
            if bullet[1] > 1.12:
                self.bullets.remove(bullet)

        if self.boss is not None:
            boss = self.boss
            boss[4] += dt
            boss[0] = 0.5 + math.sin(boss[4] * 0.9) * 0.31
            boss[5] += dt
            if boss[5] >= max(0.48, 1.15 - self.level * 0.025):
                boss[5] = 0.0
                shot_speed = 0.25 + self.level * 0.012
                for offset in (-0.18, 0.0, 0.18):
                    self.boss_shots.append([boss[0], boss[1] - 0.08, offset, -shot_speed])

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
            shot[0] += shot[2] * dt
            shot[1] += shot[3] * dt
            if shot[1] < -0.08 or shot[0] < -0.08 or shot[0] > 1.08:
                self.boss_shots.remove(shot)
            elif abs(shot[1] - 0.14) < 0.045 and abs(shot[0] - self.player_x) < 0.038:
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
            elif (abs(meteor[1] - 0.14) < 0.065 + 0.012 * meteor[2]
                  and abs(meteor[0] - self.player_x) < 0.035 + 0.012 * meteor[2]):
                self.asteroids.remove(meteor)
                if self.shield_time > 0:
                    self.shield_time = 0.0
                    self.explode(meteor[0], meteor[1], 26)
                else:
                    self.lives -= 1
                    self.explode(meteor[0], meteor[1], 20)

        for star in self.stars[:]:
            star[1] -= dt * 0.3
            if star[1] < -0.08:
                self.stars.remove(star)
            elif star[1] < 0.17 and abs(star[0] - self.player_x) < 0.075:
                self.stars.remove(star)
                self.score += 15
                self.explode(star[0], star[1], 9)

        for pickup in self.powerups[:]:
            pickup[1] -= dt * 0.24
            if pickup[1] < -0.08:
                self.powerups.remove(pickup)
            elif pickup[1] < 0.19 and abs(pickup[0] - self.player_x) < 0.085:
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

        boss_text = f"   BOSS {self.boss[2]}/{self.boss[3]}" if self.boss else ""
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

    def draw_centered_canvas_text(self, text, center_x, center_y, font_size, color):
        label = CoreLabel(text=text, font_size=font_size, bold=True, color=color)
        label.refresh()
        texture = label.texture
        Color(1, 1, 1, 1)
        Rectangle(texture=texture,
                  pos=(center_x - texture.width / 2, center_y - texture.height / 2),
                  size=texture.size)

    def draw_home_menu(self, w, h):
        # A canvas-native menu is always drawn above the space background.
        panel_w, panel_h = w * 0.82, h * 0.66
        panel_x, panel_y = self.x + (w - panel_w) / 2, self.y + h * 0.12
        Color(0.005, 0.018, 0.055, 0.82)
        Rectangle(pos=(panel_x, panel_y), size=(panel_w, panel_h))
        Color(0.12, 0.72, 1, 0.85)
        Line(rectangle=(panel_x, panel_y, panel_w, panel_h), width=1.4)

        self.draw_centered_canvas_text("STAR DODGER", self.x + w * 0.5,
                                       self.y + h * 0.80, max(30, w * 0.075),
                                       (0.88, 0.97, 1, 1))
        self.draw_centered_canvas_text("DODGE THE METEORS. COLLECT THE STARS.",
                                       self.x + w * 0.5, self.y + h * 0.70,
                                       max(10, w * 0.025), (0.48, 0.86, 1, 1))
        status = f"BEST SCORE  {self.best_score}" if self.best_score else "READY FOR YOUR NEXT RUN?"
        self.draw_centered_canvas_text(status, self.x + w * 0.5,
                                       self.y + h * 0.57, max(13, w * 0.031),
                                       (0.85, 0.92, 1, 1))

        buttons = (
            ("PLAY", 0.49, (0.04, 0.55, 0.86, 1)),
            ("SETTINGS", 0.37, (0.08, 0.22, 0.40, 1)),
            ("HOW TO PLAY", 0.25, (0.08, 0.22, 0.40, 1)),
        )
        for label, cy, fill in buttons:
            bx, by = self.x + w * 0.18, self.y + h * (cy - 0.042)
            bw, bh = w * 0.64, h * 0.084
            Color(*fill)
            Rectangle(pos=(bx, by), size=(bw, bh))
            Color(0.22, 0.82, 1, 0.95)
            Line(rectangle=(bx, by, bw, bh), width=1.25)
            self.draw_centered_canvas_text(label, self.x + w * 0.5,
                                           self.y + h * cy, max(16, w * 0.039),
                                           (0.94, 0.98, 1, 1))
        self.draw_centered_canvas_text("TOUCH PLAY TO START",
                                       self.x + w * 0.5, self.y + h * 0.155,
                                       max(10, w * 0.024), (0.42, 0.72, 0.9, 1))

    def draw_menu_panel(self, w, h, heading, subtitle):
        panel_w, panel_h = w * 0.82, h * 0.72
        panel_x, panel_y = self.x + (w - panel_w) / 2, self.y + h * 0.10
        Color(0.005, 0.018, 0.055, 0.88)
        Rectangle(pos=(panel_x, panel_y), size=(panel_w, panel_h))
        Color(0.12, 0.72, 1, 0.9)
        Line(rectangle=(panel_x, panel_y, panel_w, panel_h), width=1.4)
        self.draw_centered_canvas_text(heading, self.x + w * 0.5,
                                       self.y + h * 0.80, max(27, w * 0.067),
                                       (0.88, 0.97, 1, 1))
        self.draw_centered_canvas_text(subtitle, self.x + w * 0.5,
                                       self.y + h * 0.70, max(11, w * 0.027),
                                       (0.48, 0.86, 1, 1))

    def draw_settings_menu(self, w, h):
        self.draw_menu_panel(w, h, "SETTINGS", "CHOOSE YOUR DIFFICULTY")
        for label, cy in (("EASY", 0.46), ("NORMAL", 0.36), ("HARD", 0.26)):
            selected = label.title() == self.difficulty
            bx, by, bw, bh = self.x + w * 0.18, self.y + h * (cy - 0.042), w * 0.64, h * 0.084
            Color(0.04, 0.55, 0.82, 1) if selected else Color(0.08, 0.22, 0.40, 1)
            Rectangle(pos=(bx, by), size=(bw, bh))
            Color(0.22, 0.82, 1, 0.95)
            Line(rectangle=(bx, by, bw, bh), width=1.25)
            self.draw_centered_canvas_text(label, self.x + w * 0.5,
                                           self.y + h * cy, max(16, w * 0.039),
                                           (0.94, 0.98, 1, 1))
        self.draw_centered_canvas_text("←  BACK TO MENU", self.x + w * 0.5,
                                       self.y + h * 0.15, max(13, w * 0.031),
                                       (0.55, 0.88, 1, 1))

    def draw_help_menu(self, w, h):
        self.draw_menu_panel(w, h, "HOW TO PLAY", "SURVIVE THE SECTORS")
        instructions = (
            "DRAG LEFT OR RIGHT TO STEER",
            "DODGE METEORS AND ENEMY FIRE",
            "COLLECT STARS AND POWER-UPS",
            "BOSSES APPEAR EVERY 5 LEVELS",
            "YOU HAVE 3 LIVES",
        )
        for index, line in enumerate(instructions):
            self.draw_centered_canvas_text(line, self.x + w * 0.5,
                                           self.y + h * (0.55 - index * 0.075),
                                           max(12, w * 0.030), (0.86, 0.94, 1, 1))
        self.draw_centered_canvas_text("←  BACK TO MENU", self.x + w * 0.5,
                                       self.y + h * 0.15, max(13, w * 0.031),
                                       (0.55, 0.88, 1, 1))

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
                px, py = self.x + self.player_x * w, self.y + h * 0.14
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

                for bx, by in self.bullets:
                    x, y = self.x + bx * w, self.y + by * h
                    Color(0.35, 0.95, 1, 1)
                    Line(points=[x, y - 12, x, y + 12], width=2.2)

                for sx, sy, vx, vy in self.boss_shots:
                    x, y = self.x + sx * w, self.y + sy * h
                    Color(1, 0.12, 0.38, 0.95)
                    Ellipse(pos=(x - 7, y - 7), size=(14, 14))
                    Color(1, 0.55, 0.72, 0.9)
                    Ellipse(pos=(x - 3, y - 3), size=(6, 6))

                if self.boss is not None:
                    bx, by, hp, max_hp, phase, attack = self.boss
                    x, y = self.x + bx * w, self.y + by * h
                    radius = min(w, h) * 0.105
                    pulse = 0.5 + 0.5 * math.sin(phase * 3.2)
                    # Layered armored silhouette with swept side fins.
                    Color(0.05, 0.72, 1.0, 0.13 + pulse * 0.10)
                    Ellipse(pos=(x - radius * 1.72, y - radius * 1.42),
                            size=(radius * 3.44, radius * 2.84))
                    Color(0.035, 0.10, 0.24, 1)
                    Triangle(points=[x - radius * 0.35, y + radius * 0.35,
                                     x - radius * 1.65, y - radius * 0.38,
                                     x - radius * 1.12, y - radius * 0.92])
                    Triangle(points=[x + radius * 0.35, y + radius * 0.35,
                                     x + radius * 1.65, y - radius * 0.38,
                                     x + radius * 1.12, y - radius * 0.92])
                    Color(0.10, 0.30, 0.58, 1)
                    Triangle(points=[x, y + radius * 1.18,
                                     x - radius * 1.28, y - radius * 0.48,
                                     x + radius * 1.28, y - radius * 0.48])
                    Color(0.22, 0.62, 0.86, 1)
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
                    Color(0.05, 0.78, 1, 0.20 + pulse * 0.18)
                    Ellipse(pos=(x - radius * 0.52, y - radius * 0.38),
                            size=(radius * 1.04, radius * 1.04))
                    Color(0.06, 0.72, 1, 1)
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
                    Color(0.18, 0.82, 1, 0.34 + pulse * 0.22)
                    Line(ellipse=(x - radius * 1.52, y - radius * 0.72,
                                  radius * 3.04, radius * 1.52), width=1.4)
                    Color(0.9, 0.98, 1, 0.8)
                    Line(points=[x - radius * 1.34, y - radius * 0.65,
                                 x - radius * 1.05, y - radius * 0.78], width=2)
                    Line(points=[x + radius * 1.34, y - radius * 0.65,
                                 x + radius * 1.05, y - radius * 0.78], width=2)
                    bar_w = w * 0.62
                    bar_x = self.x + (w - bar_w) * 0.5
                    bar_y = self.y + h * 0.91
                    Color(0.2, 0.08, 0.14, 0.95)
                    Rectangle(pos=(bar_x, bar_y), size=(bar_w, 9))
                    Color(0.05, 0.72, 1, 1)
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

                for sx, sy in self.stars:
                    x, y = self.x + sx * w, self.y + sy * h
                    Color(1, 0.78, 0.12, 0.2)
                    Ellipse(pos=(x - 17, y - 3), size=(34, 34))
                    Color(1, 0.84, 0.22, 1)
                    Ellipse(pos=(x - 8, y + 1), size=(16, 16))

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

            # Neon angular HUD: three separate panels, glowing edges and ship-shaped lives.
            if self.screen == "game":
                panel_h = max(56, h * 0.065)
                panel_y = self.y + h * 0.865
                panel_w = w * 0.29
                panel_xs = (self.x + w * 0.025, self.x + w * 0.355, self.x + w * 0.685)
                font = max(15, min(22, w * 0.034))
                for panel_x in panel_xs:
                    # Soft outer glow, dark glass fill, and clipped sci-fi corners.
                    Color(0.02, 0.38, 1, 0.16)
                    Line(points=[panel_x-2, panel_y+5, panel_x-2, panel_y+panel_h-5,
                                 panel_x+10, panel_y+panel_h+2, panel_x+panel_w-10, panel_y+panel_h+2,
                                 panel_x+panel_w+2, panel_y+panel_h-5, panel_x+panel_w+2, panel_y+5],
                         close=True, width=3.2)
                    Color(0.008, 0.025, 0.09, 0.94)
                    Rectangle(pos=(panel_x, panel_y), size=(panel_w, panel_h))
                    Color(0.10, 0.58, 1, 0.98)
                    Line(points=[panel_x, panel_y+7, panel_x, panel_y+panel_h-7,
                                 panel_x+10, panel_y+panel_h, panel_x+panel_w-10, panel_y+panel_h,
                                 panel_x+panel_w, panel_y+panel_h-7, panel_x+panel_w, panel_y+7,
                                 panel_x+panel_w-10, panel_y, panel_x+10, panel_y],
                         close=True, width=1.35)

                # Extra-bright level readout, deliberately larger and centered in its own panel.
                self.draw_canvas_text(f"LEVEL {self.level}",
                                      panel_xs[0] + 9, panel_y + panel_h * 0.29,
                                      font + 2, (0.78, 0.97, 1, 1))

                # Three tiny cyan ships communicate remaining lives at a glance.
                life_cx = panel_xs[1] + panel_w * 0.5
                life_gap = min(25, panel_w * 0.23)
                ship_y = panel_y + panel_h * 0.53
                for life_index in range(3):
                    sx = life_cx + (life_index - 1) * life_gap
                    if life_index < self.lives:
                        Color(0.02, 0.65, 1, 0.22)
                        Ellipse(pos=(sx-10, ship_y-11), size=(20, 22))
                        Color(0.22, 0.88, 1, 1)
                        Triangle(points=[sx, ship_y+10, sx-7, ship_y-7, sx+7, ship_y-7])
                        Color(0.9, 0.99, 1, 1)
                        Line(points=[sx, ship_y+5, sx, ship_y-3], width=1.1)
                    else:
                        Color(0.25, 0.38, 0.55, 0.5)
                        Line(points=[sx, ship_y+8, sx-7, ship_y-7, sx+7, ship_y-7],
                             close=True, width=1)

                self.draw_canvas_text(f"SCORE {self.score}",
                                      panel_xs[2] + 10, panel_y + panel_h * 0.30,
                                      font, (0.56, 1, 0.91, 1))

                # No on-screen steering arrows: the whole playfield is touch-and-drag.
            Color(0.12, 0.68, 1, 0.35)
            Line(points=[self.x, self.y + 1, self.x + w, self.y + 1], width=1)

            if self.screen == "home":
                self.draw_home_menu(w, h)
            elif self.screen == "settings":
                self.draw_settings_menu(w, h)
            elif self.screen == "help":
                self.draw_help_menu(w, h)


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