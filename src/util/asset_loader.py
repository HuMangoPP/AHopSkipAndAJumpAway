import pygame as pg
import os

SCALE = 2

def load_assets(path='./assets') -> dict[str, dict[str, pg.Surface]]:
    sprite_types = os.listdir(os.path.join(path))
    sprites = {}
    for sprite_type in sprite_types:
        sprites_of_type = os.listdir(os.path.join(path, sprite_type))
        sprite_group = {}
        for sprite in sprites_of_type:
            if sprite.split('.')[1] == 'png':
                img = pg.image.load(os.path.join(path, sprite_type, sprite)).convert()
                img.set_colorkey((0, 0, 0))
                width, height = img.get_size()
                img = pg.transform.scale(img, (2*width, 2*height))
                sprite_group[sprite.split('.')[0]] = img
        
        sprites[sprite_type] = sprite_group
    
    return sprites