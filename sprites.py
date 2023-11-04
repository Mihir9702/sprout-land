import pygame
from settings import *
from random import randint, choice
from timer import Timer


class Generic(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups, z=LAYERS['main']):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft=pos)
        self.z = z
        self.hitbox = self.rect.copy().inflate(-self.rect.width *
                                               0.2, -self.rect.height * 0.75)


class Interaction(Generic):
    def __init__(self, pos, size, groups, name):
        super().__init__(pos, pygame.Surface(size), groups)
        self.name = name
        self.hitbox = self.rect.copy().inflate(
            (-self.rect.width * 0.2),
            (-self.rect.height * 0.75))


class Water(Generic):
    def __init__(self, pos, frames, groups):

        # animation setup
        self.frames = frames
        self.frame_index = 0

        # sprite setup
        super().__init__(
            pos=pos,
            surf=self.frames[self.frame_index],
            groups=groups,
            z=LAYERS['water'])

    def animate(self, dt):
        self.frame_index += 5 * dt
        if self.frame_index >= len(self.frames):
            self.frame_index = 0
        self.image = self.frames[int(self.frame_index)]

    def update(self, dt):
        self.animate(dt)


class WildFlower(Generic):
    def __init__(self, pos, surf, groups):
        super().__init__(pos, surf, groups)
        self.hitbox = self.rect.copy().inflate(-20, -self.rect.height * 0.9)


class Particle(Generic):
    def __init__(self, pos, surf, groups, z, duration=200):
        super().__init__(pos, surf, groups, z)
        self.start_time = pygame.time.get_ticks()
        self.duration = duration

        mask_surf = pygame.mask.from_surface(self.image)
        new_surf = mask_surf.to_surface()
        new_surf.set_colorkey('black')
        self.image = new_surf

    def update(self, dt):
        current_time = pygame.time.get_ticks()
        if current_time - self.start_time > self.duration:
            self.kill()


class Tree(Generic):
    def __init__(self, pos, surf, groups, name, player_add):
        super().__init__(pos, surf, groups)

        # tree attr
        self.health = 5
        self.alive = True
        self.stump_path = f'./assets/stumps/{name.lower()}.png'
        self.stump_surf = pygame.image.load(self.stump_path).convert_alpha()

        # apples
        self.apple_path = './assets/fruit/apple.png'
        self.apples_surf = pygame.image.load(self.apple_path).convert_alpha()
        self.apples_pos = APPLE_POS[name]
        self.apple_groups = self.groups()[0]
        self.apple_sprites = pygame.sprite.Group()
        self.create_fruit()

        self.player_add = player_add

        # sounds
        self.axe_sound = pygame.mixer.Sound('./audio/axe.mp3')

    def damage(self):
        self.health -= 1
        self.axe_sound.play()

        # remove random apple
        if len(self.apple_sprites.sprites()) > 0:
            rand_apple = choice(self.apple_sprites.sprites())
            Particle(rand_apple.rect.topleft, rand_apple.image,
                     self.apple_groups, LAYERS['fruit'], 200)
            self.player_add('apple')
            rand_apple.kill()

    def check_death(self):
        if self.health <= 0:
            Particle(self.rect.topleft, self.image,
                     self.apple_groups, LAYERS['fruit'], 300)
            self.image = self.stump_surf
            self.rect = self.image.get_rect(midbottom=self.rect.midbottom)
            self.hitbox = self.rect.copy().inflate(-10, -self.rect.height * 0.6)
            self.alive = False
            self.player_add('wood')

    def create_fruit(self):
        for pos in self.apples_pos:
            if randint(0, 10) < 2:
                x = pos[0] + self.rect.left
                y = pos[1] + self.rect.top
                Generic(pos=(x, y),
                        surf=self.apples_surf,
                        groups=[self.apple_sprites, self.apple_groups],
                        z=LAYERS['fruit'])

    def update(self, dt):
        if self.alive:
            self.check_death()
