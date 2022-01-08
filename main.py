import pygame
import os
import sys
import csv

SZ = (800, 400)


def load_image(name, colorkey=None):
    fullname = os.path.join('images', name)
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    return image


def level_data(level):
    csvfile = open(os.path.join('levels', level), newline='')
    data = list(csv.reader(csvfile, delimiter=',', quotechar='"'))
    const = [['0'] * len(data[0])] * (20 - len(data))
    for _ in data:
        const.append(_)
    return const


class Block(pygame.sprite.Sprite):
    image = load_image("block_1.png")

    def __init__(self, group, coords, size):
        super().__init__(group)
        image = pygame.transform.scale(Block.image, (size, size))
        image.set_alpha(256)
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = coords


class Spike(pygame.sprite.Sprite):
    image = load_image("obj-spike.png")

    def __init__(self, group, coords, size):
        super().__init__(group)
        image = pygame.transform.scale(Spike.image, (size, size))
        image.set_alpha(256)
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = coords


class Level:
    def __init__(self, screen, level):
        self.group = pygame.sprite.Group()
        self.screen = screen
        self.level = level_data(level)
        self.delta = 0
        self.size = SZ[1] // 20

    def render(self):
        for i in range(len(self.level)):
            for j in range(len(self.level[i])):
                if self.level[i][j] == 'b':
                    Block(self.group, (self.size * j - self.delta, self.size * i), self.size)
                if self.level[i][j] == 's':
                    Spike(self.group, (self.size * j - self.delta, self.size * i), self.size)
                if self.level[i][j] == '0':
                    pass
        self.group.draw(self.screen)
        self.group = pygame.sprite.Group()


def main():
    running = True
    screen = pygame.display.set_mode(SZ)
    clock = pygame.time.Clock()
    bg = load_image('bg.png')
    level = Level(screen, 'test_level.csv')
    screen.fill("white")
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        screen.blit(bg, (0, 0))
        level.render()
        pygame.display.flip()
        level.delta += 60 / 25
        clock.tick(60)


if __name__ == '__main__':
    main()