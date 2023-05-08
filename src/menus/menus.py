import pygame as pg
import numpy as np
import random, math

from ..entities.entity import Player, Enemies
from .popups import MusicPopup, BUTTON_COLOR, BUTTON_COLOR_HOVER, POPUP_SIZE, SHADOW_COLOR
from .popups import PausePopup

DEFAULT_FILL = (25, 30, 65)
BULLET_TIME_FILL = (25, 30, 65)
REAL_TIME_FILL = (65, 30, 25)

SCREEN_SHAKE = 0.5
ENTER_BULLET_TIME = 0.25

BUTTON_BLUE = (78, 61, 227)

FONT_COLORS = [
    
]

def create_rect(centerx: int, centery: int, width: int, height: int) -> pg.Rect:
    rect = pg.Rect(0, 0, width, height)
    rect.centerx = centerx
    rect.centery = centery 
    return rect

def draw_boundary(display: pg.Surface, display_offset: tuple[float, float], radius: float):
    boundary_surf = pg.Surface(display.get_size())
    pg.draw.circle(boundary_surf, (255, 255, 255), display_offset, radius)
    boundary_surf.set_colorkey((255, 255, 255))
    display.blit(boundary_surf, (0, 0))

class InGame:
    def __init__(self, game):
        # from Game class
        self.game = game
        self.display = game.display
        self.overlay = game.overlay
        self.graphics_engine = game.graphics_engine
        self.clock = game.clock
        self.resolution = game.resolution
        self.font = game.font
        self.sfx = game.sfx
        self.sound_system = game.sound_system

        self.crossflare_surf = pg.Surface(self.resolution)

        self.show_tutorial = True
        self.mouse_sprite = game.sprites['ui']['mouse']
        self.space_sprite = game.sprites['ui']['space']
        self.boundary_radius = 1000

        self.pause_popup = PausePopup(game, self)
        self.show_pause = False
        self.pause_grow = 0
        self.paused = False

        # assets
        self.crosshair = self.game.sprites['ui']['crosshair']
        self.crosshair_size = self.crosshair.get_size()

        # constants
        self.resolve_interval = 1

        self.on_load()
    
    def on_load(self):
        self.particle_groups = []
        self.bullets = []
        add_particle_group = lambda particle_group : self.particle_groups.append(particle_group)
        self.player = Player((0, 0), add_particle_group, self.sfx, self.sound_system)
        self.enemies = Enemies(5, lambda bullet : self.bullets.append(bullet), add_particle_group,
                               self.show_tutorial)

        # game state management
        self.resolve_enemy_actions = False
        self.time_spent_in_bullet_time = 0
        self.resolve_time = 0
        self.enter_bullet_time_time = 0
        self.screen_shake = 0
        self.shake_offset = [0, 0]

        self.transitioning = True
        self.show_pause = False

        # app state management
        self.game.score = 0
        self.game.kill_chain = 0
        self.game.score_add = 100
        self.countdown = 5
        self.dead = False
        self.death_countdown = 2

    def get_display_offset(self) -> tuple[float, float]:
        offset = np.array(self.resolution) * 0.5 - self.player.pos + np.array(self.shake_offset)
        return (offset[0], offset[1])
    
    def update(self) -> dict:
        events = pg.event.get()
        for event in events:
            if event.type == pg.QUIT:
                return {
                    'exit': True
                }
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                if self.show_pause:
                    self.show_pause = False
                else:
                    self.show_pause = True
                    self.paused = True
                    self.pause_grow = 0
            if self.countdown <= 0 and not self.dead and not self.transitioning and not self.paused:
                if event.type == pg.MOUSEBUTTONUP or (event.type == pg.KEYDOWN and event.key == pg.K_SPACE):
                    if self.player.bullet_time:
                        kills = self.player.take_turn(self.enemies, self.boundary_radius)
                        if kills != -1:
                            if kills == 0:
                                self.resolve_enemy_actions = True
                            if self.resolve_enemy_actions:
                                self.game.score_add = 100
                                self.game.kill_chain = 0
                            else:
                                for i in range(kills):
                                    self.sound_system.queue_new_sound(self.sfx['kill'][self.game.kill_chain])
                                    self.game.score += self.game.score_add * (1 + self.game.minimum_bullet_time)
                                    self.game.score_add += 50
                                    self.game.kill_chain = min(self.game.kill_chain + 1, 4)
                                self.time_spent_in_bullet_time = self.game.minimum_bullet_time
                            self.screen_shake = SCREEN_SHAKE
        
        dt = self.clock.get_time() / 1000
        if self.countdown <= 0 and not self.dead and not self.transitioning and not self.paused:
            # these should not be influenced by bulletime
            # screen shake
            if self.screen_shake > 0:
                self.screen_shake -= dt
                self.shake_offset = [
                    random.uniform(0, 8) - 4,
                    random.uniform(0, 8) - 4,
                ]

            [particle_group.update(dt) for particle_group in self.particle_groups]

            # enemies catch up from bullet time
            if self.resolve_enemy_actions:
                self.time_spent_in_bullet_time -= dt
                self.enemies.update(dt, self.player.pos)
                
                if self.time_spent_in_bullet_time <= 0:
                    self.time_spent_in_bullet_time = 0
                    self.resolve_enemy_actions = False
            # player is in bullet time or are entering bullet time
            else:
                self.time_spent_in_bullet_time += dt
                if not self.player.bullet_time:
                    self.enter_bullet_time_time += dt
                    dt *= (1 - self.enter_bullet_time_time/ENTER_BULLET_TIME)/10
                    if self.enter_bullet_time_time >= ENTER_BULLET_TIME:
                        self.enter_bullet_time_time = 0
                        # play a sound
                        # flash the screen
                        self.player.bullet_time = True

            
            if self.player.bullet_time:
                dt /= 100
            [bullet.update(dt) for bullet in self.bullets]
            [self.bullets.pop(i) for i in range(len(self.bullets)-1, -1, -1) if self.bullets[i].is_dead()]

            self.dead = self.player.check_hit(self.bullets)
            
            m_relpos = np.array(pg.mouse.get_pos()) - np.array(self.resolution) * 0.5
            self.player.update_shadow(math.atan2(m_relpos[1], m_relpos[0]))
        elif self.transitioning:
            # do nothing
            self.transitioning = bool(self.game.transition)
        else:
            if self.paused:
                if self.show_pause:
                    self.pause_grow = min(self.pause_grow + 2*dt, 1)
                    retval = self.pause_popup.update(events)
                    if retval and retval['goto'] == 'start':
                        return {
                            'exit': False,
                            'goto': 'start'
                        }
                    if retval and retval['goto'] == 'game':
                        self.show_pause = False
                else:
                    self.pause_grow -= 2*dt
                    if self.pause_grow <= 0:
                        self.pause_grow = 0
                        self.paused = False
                        self.countdown = 5
                return {}
            [particle_group.update(dt) for particle_group in self.particle_groups]

            if self.countdown > 0:
                prev_count = self.countdown
                self.countdown -= dt
                if math.ceil(prev_count) != math.ceil(self.countdown):
                    self.sfx['countdown'].play()

            if self.dead:
                self.player.death()
                self.player.death_particles.update(dt)
                self.death_countdown -= dt
                self.shake_offset = [
                    random.uniform(0, 8) - 4,
                    random.uniform(0, 8) - 4,
                ]
                if self.death_countdown < 0:
                    if not self.show_tutorial:
                        self.game.highscore = max(self.game.highscore, self.game.score)
                    else:
                        self.show_tutorial = False
                        self.transitioning = True
                    return {
                        'exit': False,
                        'goto': 'replay'
                    }
        return {}
    
    def render(self):
        if self.player.bullet_time:
            self.display.fill(BULLET_TIME_FILL)
        else:
            self.display.fill(REAL_TIME_FILL)

        display_offset = self.get_display_offset()
        draw_boundary(self.display, display_offset, self.boundary_radius)

        self.crossflare_surf.fill((0, 0, 0, 0))
        self.player.render(self.crossflare_surf, display_offset)
        self.enemies.render(self.crossflare_surf, display_offset)
        [bullet.render(self.crossflare_surf, display_offset) for bullet in self.bullets]
        [particle_group.render(self.crossflare_surf, display_offset) for particle_group in self.particle_groups]
        self.graphics_engine.render(self.crossflare_surf, self.crossflare_surf.get_rect(), 
                                    shader='gaussian_blur')

        if self.countdown > 0:
            self.font.render(self.overlay, f'{math.ceil(self.countdown)}', 
                                self.resolution[0]/2, self.resolution[1]/2, (255, 255, 255),
                                50, 'center')
        if self.resolve_enemy_actions or not self.player.bullet_time:
            self.font.render(self.overlay, f'{round(self.time_spent_in_bullet_time * 1000)} ms',
                            self.resolution[0]/2, self.resolution[1]-50, (200, 100, 100), 20, 'center')
        else:
            self.font.render(self.overlay, f'{round(self.time_spent_in_bullet_time * 1000)} ms',
                            self.resolution[0]/2, self.resolution[1]-50, (100, 100, 200), 20, 'center')

        self.font.render(self.overlay, f'{self.game.score}', 
                            self.resolution[0]-25-self.font.text_width(f'{self.game.score}', 20), 
                            50, (255, 255, 255), 20, 'center')

        if self.countdown > 0 and self.show_tutorial:
            self.font.render(self.overlay, 'first, a little demo', 30, 30, 
                             (255, 255, 255), 15, 'left')
            self.font.render(self.overlay, 'press space or click the mouse to leap to your shadow', 30, 60, 
                             (255, 255, 255), 15, 'left', box_width=self.resolution[0]*3/4)

        if self.paused:
            self.pause_popup.render(self.pause_grow)

        cursor_pos = np.array(pg.mouse.get_pos()) - np.array(self.crosshair_size) * 0.5
        self.overlay.blit(self.crosshair, cursor_pos)

HOVER_TIME = 0.5

class MainMenu:
    def __init__(self, game):
        # from Game class
        self.game = game
        self.display = game.display
        self.overlay = game.overlay
        self.clock = game.clock
        self.resolution = game.resolution
        self.cursor = game.cursor
        self.font = game.font

        # buttons
        width, height = self.resolution
        self.title_card = self.render_title()

        self.start_btn = create_rect(width/2, height*3/5, width/2, height/5)
        self.start_btn_hover = False
        self.start_btn_opacity = 0

        self.exit_btn = create_rect(width/2, height*4/5, width/2, height/5)
        self.exit_btn_hover = False
        self.exit_btn_opacity = 0

        self.note_icon = game.sprites['ui']['note']
        self.music_btn = create_rect(POPUP_SIZE, POPUP_SIZE, POPUP_SIZE, POPUP_SIZE)
        self.btn_shadow = self.music_btn.copy()
        self.btn_shadow.left -= 10
        self.btn_shadow.top -= 10
        self.music_popup_wipe = 0
        self.music_popup = MusicPopup(game, self)
        self.show_music_popup = False

    def update(self):
        events = pg.event.get()
        for event in events:
            if event.type == pg.QUIT:
                return {
                    'exit': True,
                }
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                return {
                    'exit': True,
                }
            if event.type == pg.MOUSEMOTION:
                if self.start_btn.collidepoint(event.pos):
                    self.start_btn_hover = True
                else:
                    self.start_btn_hover = False
                
                if self.exit_btn.collidepoint(event.pos):
                    self.exit_btn_hover = True
                else:
                    self.exit_btn_hover = False
                
                if self.music_btn.collidepoint(event.pos):
                    self.show_music_popup = True

            if event.type == pg.MOUSEBUTTONDOWN:
                if self.game.transition == 0:
                    if self.start_btn.collidepoint(event.pos):
                        return {
                            'exit': False,
                            'goto': 'tutorial'
                        }
                    if self.exit_btn.collidepoint(event.pos):
                        return {
                            'exit': True,
                        }

        dt = self.clock.get_time() / 1000
        if self.start_btn_hover:
            self.start_btn_opacity = min(self.start_btn_opacity + dt, HOVER_TIME)
        else:
            self.start_btn_opacity = max(self.start_btn_opacity - dt, 0)
        if self.exit_btn_hover:
            self.exit_btn_opacity = min(self.exit_btn_opacity + dt, HOVER_TIME)
        else:
            self.exit_btn_opacity = max(self.exit_btn_opacity - dt, 0)

        if self.show_music_popup:
            self.music_popup_wipe = min(self.music_popup_wipe + 2*dt, 1)
            self.show_music_popup = self.music_popup.update(events)
        else:
            self.music_popup_wipe = max(self.music_popup_wipe - 2*dt, 0)

        self.cursor.update(dt)  

        return {}
    
    def render_title(self) -> pg.Surface:
        fontsize = 60
        line_height = self.font.text_height('a', fontsize)
        hop = pg.Surface((
            self.font.text_width('a hop', fontsize),
            line_height
        ))
        self.font.render(hop, 'a hop', hop.get_width()/2, hop.get_height()/2,
                         (255, 255, 255), fontsize, 'center')
        hop.set_colorkey((0, 0, 0))
        skip = pg.Surface((
            self.font.text_width('skip', fontsize),
            line_height
        ))
        self.font.render(skip, 'skip', skip.get_width()/2, skip.get_height()/2,
                         (255, 255, 255), fontsize, 'center')
        skip.set_colorkey((0, 0, 0))
        anda = pg.Surface((
            self.font.text_width('and', fontsize),
            line_height
        ))
        self.font.render(anda, 'and', anda.get_width()/2, anda.get_height()/2,
                         (255, 255, 255), fontsize, 'center')
        anda.set_colorkey((0, 0, 0))
        anda = pg.transform.rotate(anda, 90)
        jump = pg.Surface((
            self.font.text_width('ajump', fontsize),
            line_height
        ))
        jump.set_colorkey((0, 0, 0))
        self.font.render(jump, 'ajump', jump.get_width()/2, jump.get_height()/2,
                         (255, 255, 255), fontsize, 'center')
        away = pg.Surface((
            self.font.text_width('away', fontsize),
            line_height
        ))
        self.font.render(away, 'away', away.get_width()/2, away.get_height()/2,
                         (255, 255, 255), fontsize, 'center')
        away.set_colorkey((0, 0, 0))
        

        title_card = pg.Surface((self.resolution[0], self.resolution[1]/3))
        title_card.set_colorkey((0, 0, 0))
        textbox = anda.get_rect()
        textbox.centerx = self.resolution[0]/2
        textbox.centery = self.resolution[1]/6
        left, right = textbox.left, textbox.right
        centery = textbox.centery
        title_card.blit(anda, textbox)
        textbox = hop.get_rect()
        textbox.right = left
        textbox.bottom = centery
        title_card.blit(hop, textbox)
        textbox = skip.get_rect()
        textbox.right = left
        textbox.top = centery
        title_card.blit(skip, textbox)
        textbox = jump.get_rect()
        textbox.left = right
        textbox.bottom = centery
        title_card.blit(jump, textbox)
        textbox = away.get_rect()
        textbox.left = right
        textbox.top = centery
        title_card.blit(away, textbox)

        return title_card

    def render(self):
        self.display.fill(DEFAULT_FILL)

        start_btn_surf = pg.Surface(self.start_btn.size)
        start_btn_surf.fill(BUTTON_BLUE)
        start_btn_surf.set_alpha(self.start_btn_opacity * 255)
        self.display.blit(start_btn_surf, self.start_btn)
        self.font.render(self.display, 'start', self.start_btn.centerx, self.start_btn.centery,
                            (255, 255, 255), 40, style='center')
        
        exit_btn_surf = pg.Surface(self.exit_btn.size)
        exit_btn_surf.fill(BUTTON_BLUE)
        exit_btn_surf.set_alpha(self.exit_btn_opacity * 255)
        self.display.blit(exit_btn_surf, self.exit_btn)
        self.font.render(self.display, 'exit', self.exit_btn.centerx, self.exit_btn.centery,
                            (255, 255, 255), 40, style='center')
        
        pg.draw.rect(self.display, SHADOW_COLOR, self.btn_shadow)
        if self.show_music_popup:
            pg.draw.rect(self.overlay, BUTTON_COLOR_HOVER, self.music_btn)
        else:
            pg.draw.rect(self.overlay, BUTTON_COLOR, self.music_btn)
        self.music_popup.render(self.music_popup_wipe)

        drawpos = np.array(self.music_btn.center) - np.array(self.note_icon.get_size())/2
        self.overlay.blit(self.note_icon, drawpos)

        self.display.blit(self.title_card, (0, self.resolution[1]/7))

        self.cursor.render(self.display)

class TutorialMenu:
    def __init__(self, game):
        # Game class
        self.game = game
        self.display = game.display
        self.resolution = game.resolution
        self.font = game.font
        self.clock = game.clock
        self.cursor = game.cursor

        width, height = self.resolution
        self.back_btn = create_rect(width*5/6, 50, width/6, 75)
        self.back_btn_hover = False
        self.back_btn_opacity = 0

        self.tutorial_text_state = -1
        self.tutorial_text_opacity = 0
        self.tutorial_text_wait = 0

        self.tutorial_text = [
            'the world is in slow motion... or is it?',
            'use the space key or mouse to move around. kills reset your movement, allowing you to chain your attacks.',
            'take as long as you want...',
            '...but be careful, you might find that you will eventually run out of time...'
        ]

        self.tutorial_scene = {
            'player': [[width*2/3, height/2], (0, 0, 255), 20],
            'enemies': [
                [[width*2/3+100, height/2+100], (255, 0, 0), 20],
                [[width*2/3-100, height/2-100], (255, 0, 0), 20],
            ],
            'bullets': [
                [np.array([width*2/3+100, height/2+100]) + 100*np.array([math.cos(2*math.pi/10*i), math.sin(2*math.pi/10*i)]),
                    (200, 0, 0), 5]
                for i in range(10)
            ]
        }

    def update(self):
        events = pg.event.get()
        for event in events:
            if event.type == pg.QUIT:
                return {
                    'exit': True
                }
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                return {
                    'exit': False,
                    'goto': 'start'
                }
            if event.type == pg.MOUSEMOTION:
                if self.back_btn.collidepoint(event.pos):
                    self.back_btn_hover = True
                else:
                    self.back_btn_hover = False
            if event.type == pg.MOUSEBUTTONDOWN:
                if self.game.transition == 0:
                    if self.back_btn.collidepoint(event.pos):
                        return {
                        'exit': False,
                        'goto': 'start'
                    }
                    else:
                        return {
                        'exit': False,
                        'goto': 'game'
                    }
        
        dt = self.clock.get_time() / 1000
        if self.back_btn_hover:
            self.back_btn_opacity = min(self.back_btn_opacity + dt, HOVER_TIME)
        else:
            self.back_btn_opacity = max(self.back_btn_opacity - dt, 0)
        
        if self.tutorial_text_state > 0:
            self.tutorial_text_opacity += dt
            if self.tutorial_text_opacity >= 0.5:
                self.tutorial_text_wait += dt
                if self.tutorial_text_wait > 1:
                    self.tutorial_text_state = -1
        else:
            self.tutorial_text_opacity -= dt
            if self.tutorial_text_opacity <= 0:
                self.tutorial_text_state = 1
                self.tutorial_text_wait = 0
    
        self.cursor.update(dt)

        return {}

    def render(self):
        self.display.fill(DEFAULT_FILL)
        # basic buttons and text
        self.font.render(self.display, 'how to play', 50, 50, (255, 255, 255), 30)
        self.font.render(self.display, 'click anywhere to continue', self.resolution[0]/2, self.resolution[1]-50, 
                            (255, 255, 255), 15, 'center', self.tutorial_text_opacity * 255)
        back_btn_surf = pg.Surface(self.back_btn.size)
        back_btn_surf.fill(BUTTON_BLUE)
        back_btn_surf.set_alpha(self.back_btn_opacity * 255)
        self.display.blit(back_btn_surf, self.back_btn)
        self.font.render(self.display, 'back', self.back_btn.centerx, self.back_btn.centery,
                            (255, 255, 255), 25, 'center')
        
        # tutorial text
        text_top = self.resolution[1]/5
        text_size = 17
        box_width = self.resolution[0]*3/5
        for i, text in enumerate(self.tutorial_text):
            color = (255, 255, 255)
            self.font.render(self.display, text, 
                            50, text_top, color, text_size,
                            box_width=box_width)
            text_top += (self.font.text_height(text, text_size, box_width) + 25)
        
        pg.draw.circle(self.display, self.tutorial_scene['player'][1], self.tutorial_scene['player'][0],
                        self.tutorial_scene['player'][2])
        for enemy_in_tutorial in self.tutorial_scene['enemies']:
            pg.draw.circle(self.display, enemy_in_tutorial[1], enemy_in_tutorial[0], enemy_in_tutorial[2])
        # print(self.tutorial_scene['bullets'])
        for bullet_in_tutorial in self.tutorial_scene['bullets']:
            pg.draw.circle(self.display, bullet_in_tutorial[1], bullet_in_tutorial[0], bullet_in_tutorial[2])
        self.cursor.render(self.display)

class ReplayMenu:
    def __init__(self, game):
        # Game class
        self.game = game
        self.display = game.display
        self.resolution = game.resolution
        self.font = game.font
        self.clock = game.clock
        self.cursor = game.cursor
    
        width, height = self.resolution
        self.replay_btn = create_rect(width/4, height*5/6, width/3, height/6)
        self.replay_btn_hover = False
        self.replay_btn_opacity = 0

        self.menu_btn = create_rect(width*3/4, height*5/6, width/3, height/6)
        self.menu_btn_hover = False
        self.menu_btn_opacity = 0

        self.diff_track = create_rect(width/2, height*2/3, 400, 10)
        self.diff_slider = create_rect(self.diff_track.left+self.game.minimum_bullet_time*self.diff_track.width, 
                                       height*2/3, 20, 20)
        self.diff_slider_hover = False
        self.diff_slider_follow = False
        self.slider_text = 'this controls the timer reset after any kill and awards more points'
        self.slider_text_y = self.diff_track.top - self.font.text_height(self.slider_text, 15, width/2) - 10
 
    def update(self):
        events = pg.event.get()
        for event in events:
            if event.type == pg.QUIT:
                return {
                        'exit': True
                    }
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                return {
                        'exit': False,
                        'goto': 'start'
                    }
            if event.type == pg.MOUSEMOTION:
                if self.replay_btn.collidepoint(event.pos):
                    self.replay_btn_hover = True
                else:
                    self.replay_btn_hover = False
                
                if self.menu_btn.collidepoint(event.pos):
                    self.menu_btn_hover = True
                else:
                    self.menu_btn_hover = False
                
                if self.diff_slider.collidepoint(event.pos):
                    self.diff_slider_hover = True
                else:
                    self.diff_slider_hover = False
            if event.type == pg.MOUSEBUTTONDOWN:
                if self.game.transition == 0:
                    if self.replay_btn.collidepoint(event.pos):
                        return {
                            'exit': False,
                            'goto': 'game',
                        }
                    
                    if self.menu_btn.collidepoint(event.pos):
                        return {
                            'exit': True,
                        }
                    if self.diff_slider.collidepoint(event.pos):
                        self.diff_slider_follow = True
            if event.type == pg.MOUSEBUTTONUP:
                if self.diff_slider_follow:
                    self.diff_slider_follow = False
                    slider_value = max(min(event.pos[0] - self.diff_track.left, self.diff_track.right), 0) / self.diff_track.width
                    self.game.minimum_bullet_time = slider_value

        dt = self.clock.get_time() / 1000
        if self.replay_btn_hover:
            self.replay_btn_opacity = min(self.replay_btn_opacity + dt, HOVER_TIME)
        else:
            self.replay_btn_opacity = max(self.replay_btn_opacity - dt, 0)
        
        if self.menu_btn_hover:
            self.menu_btn_opacity = min(self.menu_btn_opacity + dt, HOVER_TIME)
        else:
            self.menu_btn_opacity = max(self.menu_btn_opacity - dt, 0)

        if self.diff_slider_follow:
            self.diff_slider.centerx = min(max(pg.mouse.get_pos()[0], self.diff_track.left), self.diff_track.right)

        self.cursor.update(dt)

        return {}

    def render(self):
        width, height = self.resolution
        self.display.fill(DEFAULT_FILL)
        self.font.render(self.display, 'game over', self.resolution[0]/2, 75, (255, 255, 255), 50, 'center')

        self.font.render(self.display, f'highscore: {self.game.highscore}', width/2, height/4,
                            (255, 255, 255), 25, 'center')
        self.font.render(self.display, f'score: {self.game.score}', width/2, height/3, 
                            (255, 255, 255), 25, 'center')

        replay_btn_surf = pg.Surface(self.replay_btn.size)
        replay_btn_surf.fill(BUTTON_BLUE)
        replay_btn_surf.set_alpha(self.replay_btn_opacity * 255)
        self.display.blit(replay_btn_surf, self.replay_btn)
        self.font.render(self.display, 'replay', self.replay_btn.centerx, self.replay_btn.centery,
                        (255, 255, 255), 25, 'center')

        menu_btn_surf = pg.Surface(self.menu_btn.size)
        menu_btn_surf.fill(BUTTON_BLUE)
        menu_btn_surf.set_alpha(self.menu_btn_opacity * 255)
        self.display.blit(menu_btn_surf, self.menu_btn)
        self.font.render(self.display, 'exit', self.menu_btn.centerx, self.menu_btn.centery,
                        (255, 255, 255), 25, 'center')
        
        self.font.render(self.display, self.slider_text,
                         self.diff_track.left, self.slider_text_y, (255, 255, 255),
                         15, 'left', box_width=self.resolution[0]/2)
        pg.draw.rect(self.display, (78, 49, 170), self.diff_track)
        pg.draw.circle(self.display, (50, 130, 184), self.diff_slider.center, self.diff_slider.width/2)
        if self.diff_slider_follow or self.diff_slider_hover:
            pg.draw.circle(self.display, (200, 200, 255), self.diff_slider.center, self.diff_slider.width/2, 5)
        
        self.cursor.render(self.display)

class DisclaimerIntro:
    def __init__(self, game):
        # Game class
        self.game = game
        self.display = game.display
        self.resolution = game.resolution
        self.font = game.font
        self.clock = game.clock
    

        self.cursor = create_rect(0, 0, 10, 10)
        self.photosensitivity_disclaimer = 'A very small percentage of people may experience a seizure when exposed to certain visual images, including flashing lights or patterns that may appear in video games. Even people who have no history of seizures or epilepsy may have an undiagnosed condition that can cause these photosensitive epileptic seizures while playing video games.'
        self.photosensitivity_disclaimer_second = 'Immediately stop playing and consult a doctor if you experience any symptoms.'
    
        self.web_version_msg = 'This version of the game was made to run on the web. It may contain graphical issues and suffer from fps drops.'
    
        self.font_color = (200, 100, 150)

    def update(self):
        events = pg.event.get()
        for event in events:
            if event.type == pg.QUIT:
                return {
                        'exit': True
                    }
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                return {
                        'exit': True
                    }
            if event.type == pg.MOUSEBUTTONDOWN:
                if self.game.transition == 0:
                    return {
                        'exit': False,
                        'goto': 'start'
                    }
        
        self.cursor.centerx = pg.mouse.get_pos()[0]
        self.cursor.centery = pg.mouse.get_pos()[1]
        return {}
    
    def render(self):
        width, height = self.resolution
        self.display.fill(DEFAULT_FILL)

        self.font.render(self.display, 'disclaimer', width/2, 75, self.font_color,
                         40, 'center')
        self.font.render(self.display, self.photosensitivity_disclaimer, 50, 150, self.font_color,
                         15, 'left', box_width=width-100)
        text_top = self.font.text_height(self.photosensitivity_disclaimer, 15, width-100) + 175
        self.font.render(self.display, self.photosensitivity_disclaimer_second, 50, text_top, 
                         self.font_color, 15, 'left', box_width=width-100)
        
        text_top += self.font.text_height(self.photosensitivity_disclaimer_second, 15, width-100) + 50
        # self.font.render(self.display, self.web_version_msg, 50, text_top, 
        #                  self.font_color, 15, 'left', box_width=width-100)
        
        self.font.render(self.display, 'click anywhere to continue', width/2, height-50, 
                         self.font_color, 15, 'center')

        pg.draw.circle(self.display, BUTTON_BLUE, self.cursor.center, self.cursor.width)

