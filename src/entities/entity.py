import pygame as pg
import numpy as np
import math, random

from .bullet import Bullet
from .particles import Particles, DeathParticles

ENTITY_SIZE = 20
FULL_NUM_BULLETS = 20
SHOTGUN_NUM_BULLETS = 5
SPIRAL_NUM_BULLETS = 10
MULTI_NUM_BULLETS = 5
WAVE_NUM_BULLETS = 10
CIRCLE_NUM_BULLETS = 10

def wave(pos: 'np.ndarray[np.float32]', angle: float) -> list[Bullet]:
    wave_amplitude = 20
    norm_angle = angle + math.pi/2
    bullets = []
    for i in range(WAVE_NUM_BULLETS):
        offset = wave_amplitude * math.sin(2*math.pi*i/10)
        start_pos = pos + offset * np.array([math.cos(norm_angle), math.sin(norm_angle)])
        bullets.append(Bullet(start_pos, angle, 150, 'normal', delay=i*0.05))
    return bullets

def circle(pos: 'np.ndarray[np.float32]', angle: float) -> list[Bullet]:
    radius = 30
    bullets = []
    for i in range(CIRCLE_NUM_BULLETS):
        circle_angle = 2*math.pi*i/10 + angle
        offset = radius * np.array([math.cos(circle_angle), math.sin(circle_angle)])
        start_pos = pos + radius * np.array([math.cos(angle), math.sin(angle)]) + offset
        bullets.append(Bullet(start_pos, angle, 125, 'normal'))
    return bullets

ENEMY_TYPES = {
    'shotgun': {
        'attack_interval': 1,
        'bullets': lambda pos, angle : [Bullet(pos, angle + (SHOTGUN_NUM_BULLETS//2-i) * math.pi/12, 150, 'normal') 
                                        for i in range(SHOTGUN_NUM_BULLETS)]
    },
    'full' : {
        'attack_interval': 1.5,
        'bullets': lambda pos, angle : [Bullet(pos, angle + i * 2*math.pi/FULL_NUM_BULLETS, 100, 'normal') 
                                        for i in range(FULL_NUM_BULLETS)],
    },
    'single' : {
        'attack_interval': 0.5,
        'bullets': lambda pos, angle : [Bullet(pos, angle, 200, 'normal')],
    },
    'multi': {
        'attack_interval': 0.75,
        'bullets': lambda pos, angle : [Bullet(pos, angle, 175, 'normal', delay=0.05*i) 
                                        for i in range(MULTI_NUM_BULLETS)]
    },
    'spiral' : {
        'attack_interval': 1.25,
        'bullets': lambda pos, angle : [Bullet(pos, angle + i * 2*math.pi/SPIRAL_NUM_BULLETS, 150, 'normal', delay=0.05*i) 
                                        for i in range(SPIRAL_NUM_BULLETS)],
    },
    'wave': {
        'attack_interval': 1,
        'bullets': wave,
    },
    'circle': {
        'attack_interval': 1,
        'bullets': circle,
    }
}

def draw_circle(radius: int, color: tuple[int, int, int]):
    surf = pg.Surface((2*radius, 2*radius))
    pg.draw.circle(surf, color, (radius, radius), radius)
    surf.set_colorkey((0, 0, 0))
    return surf

def swept_aabb_coll(movement: tuple[float, float], r1: pg.Rect, r2: pg.Rect):
    if movement[0] > 0:
        dx_enter = r2.left - r1.right
        dx_exit = r2.right - r1.left
    else:
        dx_enter = r2.right - r1.left
        dx_exit = r2.left - r1.right
    
    if movement[1] > 0:
        dy_enter = r2.top - r1.bottom
        dy_exit = r2.bottom - r1.top
    else:
        dy_enter = r2.bottom - r1.top
        dy_exit = r2.top - r1.bottom
    
    if movement[0] == 0:
        tx_enter = -np.inf
        tx_exit = np.inf
    else:
        tx_enter = dx_enter/movement[0]
        tx_exit = dx_exit/movement[0]

    if movement[1] == 0:
        ty_enter = -np.inf
        ty_exit = np.inf
    else:
        ty_enter = dy_enter/movement[1]
        ty_exit = dy_exit/movement[1]

    enter_time = max(tx_enter, ty_enter)
    exit_time = min(tx_exit, ty_exit)
    
    if (enter_time > exit_time) or enter_time > 1 or enter_time < 0:
        return False
    return True

class Entity:
    def __init__(self, pos: tuple[float, float], color: tuple[int, int, int] = (0, 0, 255),
                 move_speed = 150):
        self.pos = np.array(pos)
        self.color = color
        self.move_speed = move_speed

        self.surf : pg.Surface = None
        self.glow : pg.Surface = None
        self.rect : pg.Rect = None


    def update(self, dt: float): ...

    def render(self, display: pg.Surface, display_offset: tuple[float, float]):
        drawpos = np.array(self.rect.topleft) + np.array(display_offset)
        display.blit(self.surf, drawpos)
    
class Player(Entity):
    def __init__(self, pos: tuple[float, float], add_particle_group: callable,
                 sfx: dict, sound_system):
        super().__init__(pos)
        self.bullet_time = True
        self.shadow_pos = self.pos

        self.surf = draw_circle(ENTITY_SIZE, self.color)
        self.rect = self.surf.get_rect()

        self.add_particle_group = add_particle_group
        self.death_particles = DeathParticles(self.pos, self.color)

        self.sfx = sfx
        self.sound_system = sound_system

    def take_turn(self, enemies, boundary: float) -> int:
        # cannot move past boundary
        sqr_dist_from_center = self.shadow_pos @ self.shadow_pos
        if sqr_dist_from_center >= boundary**2:
            return -1
        
        shadow_offset = self.shadow_pos - self.pos
        angle = math.atan2(shadow_offset[1], shadow_offset[0])

        kills = []
        for i in range(len(enemies.enemies)):
            enemy_offset = enemies.enemies[i].pos - self.pos
            if enemy_offset @ enemy_offset >= (self.move_speed + 2*ENTITY_SIZE)**2:
                continue
            if swept_aabb_coll(shadow_offset, self.rect, enemies.enemies[i].rect):
                kills.append(i)


        enemies.kill(kills)
        
        # move
        self.pos = self.pos + shadow_offset
        self.add_particle_group(Particles(self.pos, angle))

        if not kills:
            self.bullet_time = False

        self.sound_system.queue_new_sound(self.sfx['turn'])
        
        return len(kills)

    def update_shadow(self, angle: float):
        self.shadow_pos = self.pos + self.move_speed * np.array([math.cos(angle), math.sin(angle)])

    def check_hit(self, bullets: list):
        for bullet in bullets:
            rvec = self.pos - bullet.pos
            sqr_dist = rvec @ rvec
            if sqr_dist <= ENTITY_SIZE**2:
                self.add_particle_group(Particles(self.pos, bullet.angle, groups=1))
                self.sound_system.queue_new_sound(self.sfx['hit'])
                self.death_particles.update_anchor(self.pos)
                return True
        
        return False

    def update(self, dt: float): ...

    def render(self, display: pg.Surface, display_offset: tuple[float, float]):
        self.rect.centerx = self.pos[0]
        self.rect.centery = self.pos[1]
        super().render(display, display_offset)
        # draw shadow
        shadow_drawpos = self.shadow_pos + np.array(display_offset) - np.array([ENTITY_SIZE, ENTITY_SIZE])
        display.blit(self.surf, shadow_drawpos)

        # death particles
        self.death_particles.render(display, display_offset)

        # print(f'player: {self.pos}, anchor: {self.death_particles.pos}')

    def death(self):
        self.death_particles.spawn_particles()

class Enemies:
    def __init__(self, num_enemies: int, add_bullets: callable, add_particle_group: callable,
                 in_tutorial: bool):
        self.enemies = []
        self.num_enemies = num_enemies
        self.add_bullets = add_bullets
        self.add_particle_group = add_particle_group
        if in_tutorial:
            self.test_config()
        else:
            self.starting_config()
        
        self.spawn_rate = 1
        self.spawn_time = 0
    
    def starting_config(self):
        angle = 2*math.pi/self.num_enemies
        [self.spawn_enemy(200*np.array([math.cos(angle*i), math.sin(angle*i)])) for i in range(self.num_enemies)]

    def test_config(self):
        [self.spawn_enemy((100+150*i)*np.array([1, 0])) for i in range(5)]

    def spawn_enemy(self, pos: tuple[float, float]):
        self.enemies.append(Enemy(pos, self.add_bullets, self.add_particle_group, enemy_type=random.choice(list(ENEMY_TYPES))))
        # self.enemies.append(Enemy(pos, self.add_bullets, self.add_particle_group, enemy_type='full'))

    def randomly_spawn(self):
        self.enemies.append(Enemy((random.uniform(-250, 250), random.uniform(-250, 250)),
                                  self.add_bullets, self.add_particle_group, 
                                  enemy_type=random.choice(list(ENEMY_TYPES))))

    def update(self, dt: float, ppos: tuple[float, float]):
        [enemy.update(dt, ppos) for enemy in self.enemies]

        self.spawn_time += dt
        if self.spawn_time >= self.spawn_rate:
            self.randomly_spawn()
            self.spawn_time = 0
    
    # def update_bullets(self, dt: float, slow_down: bool):
    #     if slow_down:
    #         dt /= 10
    #     [bullet.update(dt) for enemy in self.enemies for bullet in enemy.bullets]
    #     [enemy.check_bullet_lifetime() for enemy in self.enemies]

    def take_turns(self):
        [enemy.take_turn() for enemy in self.enemies]
    
    def kill(self, kills):
        [self.enemies.pop(kills[kill_index]) for kill_index in range(len(kills)-1, -1, -1)]

    def render(self, display: pg.Surface, display_offset: tuple[float, float]):
        [enemy.render(display, display_offset) for enemy in self.enemies]
        # [bullet.render(display, display_offset)  for enemy in self.enemies for bullet in enemy.bullets]

class Enemy(Entity):
    def __init__(self, pos: tuple[float, float], add_bullets: callable, 
                 add_particle_group: callable, enemy_type: str = 'spiral'):
        super().__init__(pos, color=(255, 0, 0))
        self.enemy_type = enemy_type
        self.attack_timer = 0
        self.attack_interval = ENEMY_TYPES[self.enemy_type]['attack_interval']
        self.attack_count = 0
        self.bullets : list[Bullet] = []
        self.add_bullets = add_bullets
        self.add_particle_group = add_particle_group

        self.surf = draw_circle(ENTITY_SIZE, self.color)
        self.glow = draw_circle(2*ENTITY_SIZE, (100, 50, 50))
        self.rect = self.surf.get_rect()
    
    def resolve_action(self, ppos: tuple[float, float]):
        rel = np.array(ppos) - self.pos
        angle = math.atan2(rel[1], rel[0])
        new_bullets = ENEMY_TYPES[self.enemy_type]['bullets'](self.pos, angle)
        [self.add_bullets(new_bullet) for new_bullet in new_bullets]
        self.attack_count -= 1

    def take_turn(self):
        angle = random.uniform(0, 2*math.pi)
        self.pos = self.pos + self.move_speed * np.array([math.cos(angle), math.sin(angle)])

    def update(self, dt: float, ppos: tuple[float, float]):
        self.attack_timer += dt
        if self.attack_timer > self.attack_interval:
            self.resolve_action(ppos)
            self.attack_timer = 0
    
    def render(self, display: pg.Surface, display_offset: tuple[float, float]):
        self.rect.centerx = self.pos[0]
        self.rect.centery = self.pos[1]
        super().render(display, display_offset)

        
