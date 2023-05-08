import pygame as pg

class SoundSystem:
    def __init__(self):
        self.sound_queue : list[pg.mixer.Sound] = []
    
    def queue_new_sound(self, sound: pg.mixer.Sound):
        self.sound_queue.append(sound)
    
    def play_queued_sounds(self):
        index = 0
        for sound in self.sound_queue:
            channel = sound.play()
            if not channel:
                break
            index += 1
        self.sound_queue[0:index] = []
