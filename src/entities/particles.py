import pygame as pg
import numpy as np
import random, math

NUM_PARTICLES = 5
LIFETIME = 0.5
MAJOR_AXIS = 20
MINOR_AXIS = 5
RADIUS = 15

def draw_circle(radius: float, color: tuple[int, int, int]) -> pg.Surface:
    surf = pg.Surface((2*radius, 2*radius))
    pg.draw.circle(surf, color, (radius, radius), radius)
    surf.set_colorkey((0, 0, 0))
    return surf

def get_spark(minor_axis: float, major_axis: float, pos: 'np.ndarray[np.float32]', 
              angle: float) -> list['np.ndarray[np.float32]']:
    norm_angle = angle + math.pi/2
    points = [
        pos - major_axis*3/4 * np.array([math.cos(angle), math.sin(angle)]),
        pos - minor_axis/2 * np.array([math.cos(norm_angle), math.sin(norm_angle)]),
        pos + major_axis/4 * np.array([math.cos(angle), math.sin(angle)]),
        pos + minor_axis/2 * np.array([math.cos(norm_angle), math.sin(norm_angle)]),
    ]
    return points

class Particles:
    def __init__(self, anchor: 'np.ndarray[np.float32]', angle: float, groups: int=1, glow: bool=True):
        self.anchor = anchor
        # a particle will be stored:
        # [pos: np.array, vel: np.array, color: tuple, time: float]
        self.particles = []
        self.groups = groups
        self.glow = glow
        self.angle = angle
        self.spawn_particles()

    def spawn_particles(self):
        for i in range(NUM_PARTICLES*self.groups):
            angle_range = math.pi
            angle = self.angle + math.pi + random.uniform(0, angle_range) - angle_range/2
            pos = self.anchor + MAJOR_AXIS*2/3 * np.array([math.cos(angle), math.sin(angle)])
            vel = random.uniform(50, 75) * np.array([math.cos(angle), math.sin(angle)])
            lifetime = LIFETIME
            self.particles.append([
                pos,
                vel,
                (255, 255, 255),
                lifetime
            ])
        for i in range(NUM_PARTICLES*self.groups):
            angle_range = math.pi/4
            angle = self.angle + math.pi + random.uniform(0, angle_range) - angle_range/2
            pos = self.anchor + MAJOR_AXIS*3/4 * np.array([math.cos(angle), math.sin(angle)])
            vel = random.uniform(200, 225) * np.array([math.cos(angle), math.sin(angle)])
            lifetime = LIFETIME * random.uniform(0.75, 1.25)
            self.particles.append([
                pos,
                vel,
                (255, 255, 255),
                lifetime
            ])
    
    def update(self, dt: float):
        for i in range(len(self.particles)-1, -1, -1):
            self.particles[i][0] = self.particles[i][0] + self.particles[i][1] * dt
            self.particles[i][3] -= dt
            if self.particles[i][3] <= 0:
                self.particles.pop(i)
        
    def render(self, display: pg.Surface, display_offset: tuple[float, float]):
        for particle in self.particles:
            drawpos = particle[0] + np.array(display_offset)
            minor_axis = MINOR_AXIS * particle[3] * 3
            major_axis = MAJOR_AXIS * particle[3] * 3
            angle = math.atan2(particle[1][1], particle[1][0])
            spark_points = get_spark(minor_axis, major_axis, 
                                     drawpos, angle)
            pg.draw.polygon(display, (255, 255, 255), spark_points)

            if self.glow:
                glow = draw_circle(major_axis, (10, 10, 25))
                drawpos = drawpos - np.array([major_axis, major_axis])
                display.blit(glow, drawpos, special_flags=pg.BLEND_RGB_ADD)

class DeathParticles:
    def __init__(self, anchor: 'np.ndarray[np.float32]', color: tuple[int, int, int]):
        self.anchor = anchor
        # a particle will be stored:
        # [pos: np.array, vel: np.array, time: float]
        self.particles = []
        self.color = color

    def update_anchor(self, anchor: 'np.ndarray[np.float32]'):
        self.anchor = anchor

    def spawn_particles(self):
        angle_range = 2*math.pi
        angle = 3*math.pi/2 + random.uniform(0, angle_range) - angle_range/2
        pos = np.array(self.anchor) + MAJOR_AXIS * np.array([math.cos(angle), math.sin(angle)])
        vel = random.uniform(200, 250) * np.array([math.cos(angle), math.sin(angle)])
        lifetime = LIFETIME * random.uniform(0.5, 1)
        self.particles.append([
            pos,
            vel,
            lifetime
        ])
    
    def update(self, dt: float):
        for i in range(len(self.particles)-1, -1, -1):
            self.particles[i][0] = self.particles[i][0] + self.particles[i][1] * dt
            self.particles[i][2] -= dt
            if self.particles[i][2] <= 0:
                self.particles.pop(i)
    
    def render(self, display: pg.Surface, display_offset: tuple[float, float]):
        for particle in self.particles:
            drawpos = particle[0] + np.array(display_offset)
            minor_axis = MINOR_AXIS * particle[2] * 5
            major_axis = MAJOR_AXIS * particle[2] * 7
            angle = math.atan2(particle[1][1], particle[1][0])
            spark_points = get_spark(minor_axis, major_axis, 
                                     drawpos, angle)
            pg.draw.polygon(display, (255, 255, 255), spark_points)
            
            glow = draw_circle(major_axis, (10, 10, 25))
            drawpos = drawpos - np.array([major_axis, major_axis])
            display.blit(glow, drawpos, special_flags=pg.BLEND_RGB_ADD)

class CursorParticles:
    def __init__(self, groups: int=1):
        self.particles = []
        self.groups = groups
        self.spawn_rate = 0.1
        self.spawn_time = 0
        # a particle will be stored:
        # [pos: np.array, vel: np.array, color: tuple, time: float]
    
    def spawn_particles(self):
        for i in range(NUM_PARTICLES*self.groups):
            angle_range = 2*math.pi
            angle = 3*math.pi/2 + random.uniform(0, angle_range) - angle_range/2
            anchor = pg.mouse.get_pos()
            pos = np.array(anchor) + MAJOR_AXIS * np.array([math.cos(angle), math.sin(angle)])
            vel = random.uniform(200, 250) * np.array([math.cos(angle), math.sin(angle)])
            lifetime = LIFETIME * random.uniform(0.5, 1)
            self.particles.append([
                pos,
                vel,
                (255, 255, 255),
                lifetime
            ])
    
    def update(self, dt: float):
        self.spawn_time += dt
        if self.spawn_time >= self.spawn_rate:
            self.spawn_particles()
            self.spawn_time = 0

        for i in range(len(self.particles)-1, -1, -1):
            # gravity
            self.particles[i][1] = self.particles[i][1] + np.array([0, 400]) * dt
            self.particles[i][0] = self.particles[i][0] + self.particles[i][1] * dt
            self.particles[i][3] -= dt
            if self.particles[i][3] <= 0:
                self.particles.pop(i)
    
    def render(self, display: pg.Surface):
        for particle in self.particles:
            drawpos = particle[0]
            minor_axis = MINOR_AXIS * particle[3] * 5
            major_axis = MAJOR_AXIS * particle[3] * 7
            angle = math.atan2(particle[1][1], particle[1][0])
            spark_points = get_spark(minor_axis, major_axis, 
                                     drawpos, angle)
            pg.draw.polygon(display, (255, 255, 255), spark_points)

            glow = draw_circle(major_axis, (10, 10, 25))
            drawpos = drawpos - np.array([major_axis, major_axis])
            display.blit(glow, drawpos, special_flags=pg.BLEND_RGB_ADD)