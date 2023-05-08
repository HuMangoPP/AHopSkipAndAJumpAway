import pygame as pg
import moderngl as mgl
import asyncio
import sys, math

from .pymgl.graphics_engine import GraphicsEngine
from .pyfont.font import Font

from .util.asset_loader import load_assets 
from .util.sound_system import SoundSystem

from .menus.menus import InGame, MainMenu, TutorialMenu, ReplayMenu, DisclaimerIntro
from .entities.particles import CursorParticles

MENU_MAP = {
    'disclaimer': 0,
    'start': 1,
    'tutorial': 2,
    'game': 3,
    'replay': 4,
}

TRANSITION_TIME = 0.75

def create_rect(centerx: int, centery: int, width: int, height: int) -> pg.Rect:
    rect = pg.Rect(0, 0, width, height)
    rect.centerx = centerx
    rect.centery = centery 
    return rect

def screen_transition(overlay: pg.Surface, transition_time: float, type: int):
    width, height = overlay.get_size()
    if type == MENU_MAP['replay']:
        transition_progress = transition_time / TRANSITION_TIME
        radius = math.sqrt(width * width + height * height) * (1 - transition_progress)
        overlay.fill((10, 10, 10))
        pg.draw.circle(overlay, (0, 0, 0), (width/2, height/2), radius)
    else:
        transition_progress = 1.25 * transition_time / TRANSITION_TIME
        topleft = [0, 0]
        bottomleft = [0, height]
        topright = [transition_progress * width , 0]
        bottomright = [transition_progress * width - 200, height]
        points = [
            topleft, bottomleft, bottomright, topright
        ]
        overlay.fill((0, 0, 0))
        pg.draw.polygon(overlay, (10, 10, 10), points)

def screen_detransition(overlay: pg.Surface, transition_time: float, type: int):
    width, height = overlay.get_size()
    if type == MENU_MAP['replay']:
        transition_progress = transition_time / TRANSITION_TIME
        radius = math.sqrt(width * width + height * height) * (transition_progress)
        overlay.fill((10, 10, 10))
        pg.draw.circle(overlay, (0, 0, 0), (width/2, height/2), radius)
    else:
        transition_progress = 1.25 * transition_time / TRANSITION_TIME
        topleft = [transition_progress * width, 0]
        bottomleft = [transition_progress * width - 200, height]
        topright = [width, 0]
        bottomright = [width, height]
        points = [
            topleft, bottomleft, bottomright, topright
        ]
        overlay.fill((0, 0, 0))
        pg.draw.polygon(overlay, (10, 10, 10), points)

class Game:
    def __init__(self):
        # init
        pg.init()
        self.resolution = (960, 720)
        # self.display = pg.display.set_mode(self.resolution)

        pg.display.set_mode(self.resolution, pg.OPENGL | pg.DOUBLEBUF)
        self.ctx = mgl.create_context()
        self.ctx.enable(mgl.BLEND)
        self.ctx.blend_func = (
            mgl.SRC_ALPHA, mgl.ONE_MINUS_SRC_ALPHA,
        )
        self.graphics_engine = GraphicsEngine(self.ctx, self.resolution)
        self.display = pg.Surface(self.resolution)
        self.overlay = pg.Surface(self.resolution)
        self.clock = pg.time.Clock()
        self.font = Font(pg.image.load('./src/pyfont/font.png').convert())
        pg.mouse.set_visible(False)
        pg.event.set_grab(True)
        pg.display.set_caption('A Hop, Skip, and a Jump Away')

        pg.mixer.init()
        pg.mixer.set_num_channels(64)
        pg.mixer.music.load(filename='./assets/sounds/bullethell_synth.ogg')
        self.volume_level = 0.5
        pg.mixer.music.set_volume(self.volume_level)
        pg.mixer.music.play(loops=-1)
        self.sfx = {
            'hit': pg.mixer.Sound(file='./assets/sounds/death.ogg'),
            'kill': [
                pg.mixer.Sound(file=f'./assets/sounds/bullethell_kill{i+1}.ogg')
                for i in range(5)],
            'turn': pg.mixer.Sound(file='./assets/sounds/bullethell_turn.ogg'),
            'countdown': pg.mixer.Sound(file='./assets/sounds/countdown.ogg')
        }
        [sound.set_volume(0.25) for sound in self.sfx['kill']]
        [sound.fadeout(500) for sound in self.sfx['kill']]
        self.sfx['turn'].set_volume(0.3)
        self.sfx['hit'].set_volume(1)
        self.sound_system = SoundSystem()

        # for menus
        self.cursor = CursorParticles(groups=1)

        self.sprites = load_assets(path='./assets/graphics')
        self.score = 0
        self.score_add = 100
        self.highscore = 0
        self.kill_chain = 0
        self.minimum_bullet_time = 0

        self.menus = [
            DisclaimerIntro(self), 
            MainMenu(self), 
            TutorialMenu(self), 
            InGame(self), 
            ReplayMenu(self)
            ]
        self.transition = 2
        self.transition_time = 0
        self.current_menu = 0
        self.next_menu = 0
    
    async def run(self):
        while True:
            
            retval = self.menus[self.current_menu].update()
            if retval:
                if retval['exit']:
                    pg.quit()
                    sys.exit()
                else:
                    self.transition = 1
                    self.next_menu = MENU_MAP[retval['goto']]
            self.sound_system.play_queued_sounds()
            self.ctx.clear(0, 0, 0)
            dt = self.clock.get_time() / 1000

            if MENU_MAP['start'] == self.current_menu: 
                self.graphics_engine.render(self.display, self.display.get_rect(), 
                                            shader='synth_all')
            elif MENU_MAP['tutorial'] == self.current_menu or MENU_MAP['replay'] == self.current_menu:
                self.graphics_engine.render(self.display, self.display.get_rect(), 
                                            shader='synth_white')
            else:
                self.graphics_engine.render(self.display, self.display.get_rect(), shader='default')
            
            self.overlay.fill((0, 0, 0))
            self.menus[self.current_menu].render()

            if self.transition:
                self.transition_time += dt
                if self.transition_time > TRANSITION_TIME:
                    self.transition += 1
                    self.transition %= 4
                    self.transition_time = 0
                
                match(self.transition):
                    case 1:
                        screen_transition(self.overlay, self.transition_time, self.next_menu)
                    case 2:
                        self.overlay.fill((10, 10, 10))
                        if self.current_menu != self.next_menu:
                            self.current_menu = self.next_menu
                            if self.current_menu == MENU_MAP['game']:
                                self.menus[self.current_menu].on_load()
                    case 3:
                        screen_detransition(self.overlay, self.transition_time, self.next_menu)
                
            self.graphics_engine.render(self.overlay, self.overlay.get_rect(), shader='default')

            self.clock.tick()
            pg.display.flip()

            await asyncio.sleep(0)

            # pg.display.set_caption(f'fps: {self.clock.get_fps()}')
    
        