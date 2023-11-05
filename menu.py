import pygame
from settings import *
from timer import Timer


class Menu:
    def __init__(self, player, toggle_menu):

        # general setup
        self.player = player
        self.toggle_menu = toggle_menu
        self.display_surface = pygame.display.get_surface()
        self.font = pygame.font.Font('./font/LycheeSoda.ttf', 30)

        # dimensions
        self.width = 400
        self.space = 10
        self.padding = 8

        # entries
        self.options = list(self.player.item_inventory.keys()) + list(self.player.seed_inventory.keys())
        self.sell_border = len(self.player.item_inventory) - 1
        self.setup()

        # movement
        self.index = 0
        self.timer = Timer(200)

    def display_money(self):
        text_surf = self.font.render(f'${self.player.money}', False, 'black')
        text_rect = text_surf.get_rect(midbottom=(
            SCREEN_WIDTH / 2, SCREEN_HEIGHT - 20))

        pygame.draw.rect(self.display_surface, 'white',
                         text_rect.inflate(10, 10), 0, 6)
        self.display_surface.blit(text_surf, text_rect)

    def setup(self):
        self.text_surfs = []
        self.total_height = 0

        for item in self.options:
            text_surf = self.font.render(item, False, 'black')
            self.text_surfs.append(text_surf)
            self.total_height += text_surf.get_height() + (self.padding * 2)

        self.total_height += (len(self.text_surfs) - 1) * self.space
        self.menu_top = SCREEN_HEIGHT / 2 - self.total_height / 2
        self.main_rect = pygame.Rect(
            SCREEN_WIDTH / 2 - self.width / 2, self.menu_top, self.width, self.total_height)

        # buy and sell
        self.buy_text = self.font.render('buy', False, 'black')
        self.sell_text = self.font.render('sell', False, 'black')

    def input(self):
        keys = pygame.key.get_pressed()
        self.timer.update()

        if keys[pygame.K_ESCAPE] or keys[pygame.K_m]:
            self.toggle_menu()

        if not self.timer.active:
            if keys[pygame.K_UP]:
                self.index -= 1
                self.timer.start()

            if keys[pygame.K_DOWN]:
                self.index += 1
                self.timer.start()

            if keys[pygame.K_SPACE]:
                self.timer.start()

                current_item = self.options[self.index]  # item name

                # sell
                if self.index <= self.sell_border:
                    if self.player.item_inventory[current_item] > 0:
                        self.player.item_inventory[current_item] -= 1
                        self.player.money += SALE_PRICES[current_item]
                # buy
                else:
                    if self.player.money >= SALE_PRICES[current_item]:
                        self.player.seed_inventory[current_item] += 1
                        self.player.money -= SALE_PRICES[current_item]

        if self.index < 0:
            self.index = len(self.options) - 1
        elif self.index > len(self.options) - 1:
            self.index = 0

    def show_entry(self, text_surf, amount, top, selected):
        # background
        bg_rect = pygame.Rect(self.main_rect.left, top, self.width,
                              text_surf.get_height() + self.padding * 2)
        pygame.draw.rect(self.display_surface, 'white', bg_rect, 0, 4)

        # text
        text_rect = text_surf.get_rect(
            midleft=(self.main_rect.left + 20, bg_rect.centery))
        self.display_surface.blit(text_surf, text_rect)

        # amount
        amount_surf = self.font.render(str(amount), False, 'black')
        amount_rect = amount_surf.get_rect(
            midright=(self.main_rect.right - 20, bg_rect.centery))
        self.display_surface.blit(amount_surf, amount_rect)

        # selected
        if selected:
            pygame.draw.rect(self.display_surface, 'black', bg_rect, 4, 4)
            if self.index <= self.sell_border:
                pos_rect = self.sell_text.get_rect(
                    midleft=(self.main_rect.left + 150, bg_rect.centery))
                self.display_surface.blit(self.sell_text, pos_rect)  # sell
            else:
                pos_rect = self.buy_text.get_rect(
                    midleft=(self.main_rect.left + 150, bg_rect.centery))
                self.display_surface.blit(self.buy_text, pos_rect)  # buy

    def update(self):
        self.input()
        self.display_money()
        for i, text_surf in enumerate(self.text_surfs):
            top = self.main_rect.top + i * (text_surf.get_height() + (self.padding * 2) + self.space)
            amount_list = list(self.player.item_inventory()) + list(self.player.seed_inventory.values())
            amount = amount_list[i]
            self.show_entry(text_surf, amount, top, self.index == i)
            # self.display_surface(text_surf, (100, i * 50))
