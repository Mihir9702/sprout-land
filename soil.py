import pygame
from settings import *
from support import *
from os import path
from random import choice
from pytmx.util_pygame import load_pygame


class SoilTile(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft=pos)
        self.z = LAYERS['soil']


class WaterTile(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft=pos)
        self.z = LAYERS['soil water']


class Plant(pygame.sprite.Sprite):
    def __init__(self, plant_type, groups, soil, check_watered):
        super().__init__(groups)

        # setup
        self.plant_type = plant_type
        self.frames = import_folder(f'./assets/fruit/{plant_type}')
        self.soil = soil
        self.check_watered = check_watered

        # life cycle
        self.age = 0
        self.max_age = len(self.frames) - 1
        self.grow_speed = GROW_SPEED[plant_type]
        self.harvestable = False

        # sprite
        self.image = self.frames[self.age]
        self.y_offset = -16 if plant_type == 'corn' else -8
        self.rect = self.image.get_rect(
            midbottom=soil.rect.midbottom + pygame.math.Vector2(0, self.y_offset))
        self.z = LAYERS['ground plant']

    def grow(self):
        if self.check_watered(self.rect.center):
            self.age += self.grow_speed

            if int(self.age) > 0:
                self.z = LAYERS['main']

            if self.age >= self.max_age:
                self.age = self.max_age
                self.harvestable = True

            self.image = self.frames[int(self.age)]
            self.rect = self.image.get_rect(
                midbottom=self.soil.rect.midbottom + pygame.math.Vector2(0, self.y_offset))


class SoilLayer:
    def __init__(self, all_sprites):

        # sprite groups
        self.all_sprites = all_sprites
        self.soil_sprites = pygame.sprite.Group()
        self.water_sprites = pygame.sprite.Group()
        self.plant_sprites = pygame.sprite.Group()

        # graphics
        self.soil_surfs = import_folder_dict('./assets/soil')
        self.water_surfs = import_folder('./assets/soil_water')

        # audio
        self.hoe_sound = pygame.mixer.Sound('./audio/hoe.wav')
        self.hoe_sound.set_volume(0.05)

        self.plant_sound = pygame.mixer.Sound('./audio/plant.wav')
        self.plant_sound.set_volume(0.05)

        self.create_grid()
        self.create_hit_rects()

    def create_grid(self):
        ground_path = path.join('assets', 'world', 'ground.png')
        ground = pygame.image.load(ground_path)  # not showing to player
        h_tiles = ground.get_width() // TILE_SIZE
        v_tiles = ground.get_height() // TILE_SIZE

        self.grid = [[[] for col in range(h_tiles)] for row in range(v_tiles)]
        for x, y, _ in load_pygame(path.join('data', 'map.tmx')).get_layer_by_name('Farmable').tiles():
            self.grid[y][x].append('F')

    def create_hit_rects(self):
        self.hit_rects = []
        for y, row in enumerate(self.grid):
            for x, col in enumerate(row):
                if 'F' in col:
                    rect = pygame.Rect(x * TILE_SIZE, y *
                                       TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    self.hit_rects.append(rect)

    def get_hit(self, point):
        for rect in self.hit_rects:
            if rect.collidepoint(point):
                self.hoe_sound.play()

                x = rect.x // TILE_SIZE
                y = rect.y // TILE_SIZE

                if 'F' in self.grid[y][x]:
                    self.grid[y][x].append('X')
                    self.create_tiles()
                    if self.raining:
                        self.water_all()

    def create_tiles(self):
        self.soil_sprites.empty()
        for y, row in enumerate(self.grid):
            for x, col in enumerate(row):
                if 'X' in col:
                    # tile options
                    t = 'X' in self.grid[y - 1][x]
                    b = 'X' in self.grid[y + 1][x]
                    r = 'X' in row[x + 1]
                    l = 'X' in row[x - 1]

                    tile_type = 'o'

                    # all sides
                    if all((t, b, r, l)):
                        tile_type = 'x'

                    # horizontal tiles
                    if l and not any((t, r, b)):
                        tile_type = 'r'
                    if r and not any((t, l, b)):
                        tile_type = 'l'
                    if r and l and not any((t, b)):
                        tile_type = 'lr'

                    # vertical tiles
                    if t and not any((r, l, b)):
                        tile_type = 'b'
                    if b and not any((r, l, t)):
                        tile_type = 't'
                    if b and t and not any((r, l)):
                        tile_type = 'tb'

                    # corners
                    if t and r and not any((l, b)):
                        tile_type = 'bl'
                    if t and l and not any((r, b)):
                        tile_type = 'br'
                    if b and r and not any((l, t)):
                        tile_type = 'tl'
                    if b and l and not any((r, t)):
                        tile_type = 'tr'

                    # T shapes
                    if all((t, b, r)) and not l:
                        tile_type = 'tbr'
                    if all((t, b, l)) and not r:
                        tile_type = 'tbl'
                    if all((l, r, t)) and not b:
                        tile_type = 'lrt'
                    if all((l, r, b)) and not t:
                        tile_type = 'lrt'

                    SoilTile((x * TILE_SIZE, y * TILE_SIZE), self.soil_surfs[tile_type],
                             [self.all_sprites, self.soil_sprites])

    def water(self, target_pos):
        for sprite in self.soil_sprites.sprites():
            if sprite.rect.collidepoint(target_pos):
                x = sprite.rect.x // TILE_SIZE
                y = sprite.rect.y // TILE_SIZE
                self.grid[y][x].append('W')

                pos = sprite.rect.topleft
                surf = choice(self.water_surfs)

                WaterTile(pos, surf, [self.all_sprites, self.water_sprites])

    def water_all(self):
        for y, row in enumerate(self.grid):
            for x, col in enumerate(row):
                if 'X' in col and 'W' not in col:
                    col.append('W')
                    WaterTile((x * TILE_SIZE, y * TILE_SIZE), choice(self.water_surfs),
                              [self.all_sprites, self.water_sprites])

    def remove_water(self):
        # destroy all water sprites
        for sprite in self.water_sprites.sprites():
            sprite.kill()

        # clean up the grid
        for row in self.grid:
            for cell in row:
                if 'W' in cell:
                    cell.remove('W')

    def check_watered(self, pos):
        x = pos[0] // TILE_SIZE
        y = pos[1] // TILE_SIZE

        if 'W' in self.grid[y][x]:
            return True
        return False

    def plant_seed(self, target_pos, seed):
        for sprite in self.soil_sprites.sprites():
            if sprite.rect.collidepoint(target_pos):
                self.plant_sound.play()

                x = sprite.rect.x // TILE_SIZE
                y = sprite.rect.y // TILE_SIZE

                if 'P' not in self.grid[y][x]:
                    self.grid[y][x].append('P')
                    Plant(seed, [self.all_sprites, self.plant_sprites],
                          sprite, self.check_watered)

    def update_plants(self):
        for plant in self.plant_sprites.sprites():
            plant.grow()
