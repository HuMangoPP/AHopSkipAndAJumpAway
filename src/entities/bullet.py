import numpy as np
import pygame as pg
import math

LIFESPAN = 5
BULLET_SIZE = 5

def draw_circle(radius: float, color: tuple[int, int, int]) -> pg.Surface:
    surf = pg.Surface((2*radius, 2*radius))
    pg.draw.circle(surf, color, (radius, radius), radius)
    surf.set_colorkey((0, 0, 0))
    return surf

class Bullet():
    def __init__(self, pos: 'np.ndarray[np.float32]', angle: float, move_speed: float, 
                 bullet_type: str, color=(200, 0, 0), delay: float=0):
        self.pos = pos
        self.color = color
        self.angle = angle
        self.move_speed = move_speed
        self.bullet_type = bullet_type
        self.lifetime = 0
        self.delay = delay

        self.surf = draw_circle(BULLET_SIZE, (255, 255, 255))
        # pg.draw.circle(self.surf, (255, 255, 255), (BULLET_SIZE, BULLET_SIZE), BULLET_SIZE, 2)
        # self.surf = pg.Surface((2*BULLET_SIZE, 2*BULLET_SIZE))
        # self.surf.fill((255, 255, 255))
        self.rect = self.surf.get_rect()
        self.glow = draw_circle(3*BULLET_SIZE, (25, 10, 10))
        
    def update(self, dt: float):
        if self.delay > 0:
            self.delay -= dt
        else:
            self.pos = self.pos + self.move_speed * np.array([math.cos(self.angle), math.sin(self.angle)]) * dt
            self.lifetime += dt
        self.rect.centerx = self.pos[0]
        self.rect.centery = self.pos[1]
    
    def render(self, display: pg.Surface, display_offset: tuple[float, float]):
        drawpos = np.array(self.rect.topleft) + np.array(display_offset) 
        display.blit(self.surf, drawpos)
        drawpos = drawpos - 2*np.array([BULLET_SIZE, BULLET_SIZE])
        display.blit(self.glow, drawpos, special_flags=pg.BLEND_RGB_ADD)

    def is_dead(self) -> bool:
        if self.lifetime >= LIFESPAN:
            return True
        return False