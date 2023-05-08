import pygame as pg
import math

def create_rect(centerx: int, centery: int, width: int, height: int) -> pg.Rect:
    rect = pg.Rect(0, 0, width, height)
    rect.centerx = centerx
    rect.centery = centery 
    return rect

BUTTON_COLOR = (50, 130, 184)
BUTTON_COLOR_HOVER = (70, 150, 204)
POPUP_COLOR = (15, 76, 117)
TRACK_COLOR = (27, 38, 44)
SLIDER_COLOR = (58, 16, 120)
SLIDER_COLOR_HOVER = (78, 49, 170)
POPUP_SIZE = 75
SHADOW_COLOR = (78, 49, 170)

class MusicPopup:
    def __init__(self, game, menu):
        # Game and Menu classes
        self.game = game
        self.overlay = game.overlay
        self.clock = game.clock
        self.resolution = game.resolution
        self.cursor = game.cursor
        self.font = game.font
        self.menu = menu

        self.popup = create_rect(100, POPUP_SIZE, 200, POPUP_SIZE)
        self.popup.left = self.menu.music_btn.right

        self.track = create_rect(100, POPUP_SIZE, 160, 10)
        self.track.centerx = self.popup.centerx
        self.slider = create_rect(100, POPUP_SIZE, 30, 30)
        self.slider.centerx = self.track.left + self.game.volume_level * self.track.width
        self.slider_hover = False
        self.slider_follow = False
    
    def update(self, events: pg.Event):
        for event in events:
            if event.type == pg.MOUSEMOTION:
                if (not self.menu.music_btn.collidepoint(event.pos) 
                    and not self.popup.collidepoint(event.pos)
                    and not self.slider_follow):

                    return False
                if self.slider.collidepoint(event.pos):
                    self.slider_hover = True
                else:
                    self.slider_hover = False
            if event.type == pg.MOUSEBUTTONDOWN:
                if self.slider.collidepoint(event.pos):
                    self.slider_follow = True
            if event.type == pg.MOUSEBUTTONUP:
                self.slider_follow = False
                new_volume = (self.slider.centerx - self.track.left) / self.track.width
                pg.mixer.music.set_volume(new_volume)

        if self.slider_follow:
            self.slider.centerx = min(max(pg.mouse.get_pos()[0], self.track.left), self.track.right)
    
        return True
    
    def render(self, wipe: float):
        popup_rect = self.popup.copy()
        popup_rect.width = self.popup.width * wipe
        popup_rect.left += 10
        popup_rect.top += 10
        pg.draw.rect(self.overlay, SHADOW_COLOR, popup_rect)
        popup_rect.left -= 10
        popup_rect.top -= 10
        pg.draw.rect(self.overlay, POPUP_COLOR, popup_rect)

        if wipe >= 1:
            pg.draw.rect(self.overlay, TRACK_COLOR, self.track)
            if self.slider_hover or self.slider_follow:
                pg.draw.circle(self.overlay, SLIDER_COLOR_HOVER, self.slider.center, self.slider.width/2)
                pg.draw.circle(self.overlay, (200, 200, 255), self.slider.center, self.slider.width/2, 5)
            else:
                pg.draw.circle(self.overlay, SLIDER_COLOR, self.slider.center, self.slider.width/2)

class PausePopup:
    def __init__(self, game, menu):
        self.game = game
        self.display = game.display
        self.overlay = game.overlay
        self.clock = game.clock
        self.resolution = game.resolution
        self.cursor = game.cursor
        self.font = game.font
        self.menu = menu

        self.popup = create_rect(self.resolution[0]/2, self.resolution[1]/2, self.resolution[0]/2, self.resolution[1]*3/4)
        self.shadow1 = self.popup.copy()
        self.shadow1.left -= 20
        self.shadow1.top -= 20
        self.shadow2 = self.popup.copy()
        self.shadow2.left += 20
        self.shadow2.top += 20

        self.paused_text = [
            'a rare moment of reprieve.',
            'do not worry, time will not progress right now.',
            'though perhaps that is just as bad.',
            'after all, time is a precious and limited commodity. one that is gone when we need it most...'
        ]

        self.resume_btn = create_rect(self.popup.centerx-self.popup.width/4, 
                                      self.popup.bottom-50, self.popup.width/4, 50)
        self.exit_btn = create_rect(self.popup.centerx+self.popup.width/4, 
                                    self.popup.bottom-50, self.popup.width/4, 50)
        
        self.track = create_rect(self.popup.left+self.popup.width*2/3, self.popup.bottom-125, self.popup.width*2/3-50, 10)
        self.slider = create_rect(100, self.popup.bottom-125, 30, 30)
        self.slider.centerx = self.track.left + self.game.volume_level * self.track.width
        self.slider_hover = False
        self.slider_follow = False

    def update(self, events: pg.Event):
        
        for event in events:
            if event.type == pg.MOUSEMOTION:
                if self.slider.collidepoint(event.pos):
                    self.slider_hover = True
                else:
                    self.slider_hover = False
            if event.type == pg.MOUSEBUTTONDOWN:
                if self.exit_btn.collidepoint(event.pos):
                    return {
                        'goto': 'start'
                    }
                if self.resume_btn.collidepoint(event.pos):
                    return {
                        'goto': 'game'
                    }
                if self.slider.collidepoint(event.pos):
                    self.slider_follow = True
            if event.type == pg.MOUSEBUTTONUP:
                self.slider_follow = False
                new_volume = (self.slider.centerx - self.track.left) / self.track.width
                pg.mixer.music.set_volume(new_volume)

        if self.slider_follow:
            self.slider.centerx = min(max(pg.mouse.get_pos()[0], self.track.left), self.track.right)

        return {}
        
    def render(self, grow: float):
        popup_surf = pg.Surface(self.popup.size)
        radius = math.sqrt(self.popup.width/2 * self.popup.width/2 + self.popup.height/2 * self.popup.height/2) * grow
        center = (self.popup.width/2, self.popup.height/2)
        pg.draw.circle(popup_surf, SHADOW_COLOR, center, radius)
        popup_surf.set_colorkey((0, 0, 0))
        self.overlay.blit(popup_surf, self.shadow1)
        self.overlay.blit(popup_surf, self.shadow2)
        pg.draw.circle(popup_surf, POPUP_COLOR, center, radius)

        if grow >= 1:
            self.font.render(popup_surf, 'paused', self.popup.width/2, 30, 
                            (255, 255, 255), 25, 'center')
            text_top = 75
            for text in self.paused_text:
                self.font.render(popup_surf, text, 25, text_top,
                                 (255, 255, 255), 15, 'left', box_width=self.popup.width-50)
                text_top += self.font.text_height(text, 15, self.popup.width-50)
                text_top += 5
    
        self.overlay.blit(popup_surf, self.popup)

        if grow >= 1:
            pg.draw.rect(self.overlay, BUTTON_COLOR_HOVER, self.resume_btn)
            self.font.render(self.overlay, 'resume', self.resume_btn.centerx, self.resume_btn.centery,
                             (255, 255, 255), 15, 'center')
            pg.draw.rect(self.overlay, BUTTON_COLOR_HOVER, self.exit_btn)
            self.font.render(self.overlay, 'exit', self.exit_btn.centerx, self.exit_btn.centery,
                             (255, 255, 255), 15, 'center')    
            
            # self.font.render(self.display, 'volume', self.popup.left+25, text_top,
            #                  (255, 255, 255), 15, 'left')
            self.font.render(self.overlay, 'music', self.popup.left+25, self.slider.centery, 
                             (255, 255, 255), 15, 'left')
            pg.draw.rect(self.overlay, TRACK_COLOR, self.track)
            if self.slider_hover or self.slider_follow:
                pg.draw.circle(self.overlay, SLIDER_COLOR_HOVER, self.slider.center, self.slider.width/2)
                pg.draw.circle(self.overlay, (200, 200, 255), self.slider.center, self.slider.width/2, 5)
            else:
                pg.draw.circle(self.overlay, SLIDER_COLOR, self.slider.center, self.slider.width/2)
