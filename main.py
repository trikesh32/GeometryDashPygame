import pygame
import os
import sys
import csv

SZ = (800, 400)
FPS = 120
V_Y = 175
V_X = 175


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
        image = pygame.transform.scale(Spike.image, (size, size)).convert_alpha()
        image.set_alpha(256)
        self.mask = pygame.mask.from_surface(image)
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = coords


class Player(pygame.sprite.Sprite):
    image = load_image("avatar.png")

    def __init__(self, group, coords, size):
        super().__init__(group)
        image = pygame.transform.scale(Player.image, (size, size)).convert_alpha()
        image.set_alpha(256)
        self.image = image
        self.mask = pygame.mask.from_surface(image)
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = size * 3, coords


class Level:
    def __init__(self, screen, level):
        self.group = pygame.sprite.Group()
        self.player = None
        self.spikes = []
        self.screen = screen
        self.is_jumping = False
        self.is_jumping_up = False
        self.is_jumping_down = False
        self.level_elements = []
        self.start_pos_jump = None
        self.level = level_data(level)
        self.delta = 0
        self.size = SZ[1] // 20
        self.y = self.find_spawn_point() * self.size
        self.x = self.size * 3
        self.player = Player(self.group, self.y, self.size)

    def render(self):
        self.spikes = []
        self.group = pygame.sprite.Group()
        self.player = Player(self.group, self.y, self.size)
        self.level_elements = []
        for i in range(len(self.level)):
            self.level_elements.append([])
            for j in range(len(self.level[i])):
                if self.level[i][j] == 'b':
                    Block(self.group, (self.size * j - self.delta, self.size * i), self.size)
                    self.level_elements[i].append(('b', (self.size * j - self.delta, self.size * i)))
                if self.level[i][j] == 's':
                    spike = Spike(self.group, (self.size * j - self.delta, self.size * i), self.size)
                    self.level_elements[i].append(('s', (self.size * j - self.delta, self.size * i)))
                    self.spikes.append(spike)
                if self.level[i][j] == '0':
                    self.level_elements[i].append(None)
        self.group.draw(self.screen)

    def find_spawn_point(self):
        for i in range(len(self.level)):
            if self.level[i][3] != '0':
                return i - 2

    def collide_with_player(self):
        collides = []
        for i in range(len(self.level_elements)):
            for j in range(len(self.level_elements[i])):
                if self.level_elements[i][j]:
                    pos = self.level_elements[i][j][1]
                    a = [self.x, self.y, self.size, self.size]
                    b = [pos[0], pos[1], self.size, self.size]
                    ax1, ay1, ax2, ay2 = a[0], a[1], a[0] + a[2], a[1] + a[3]
                    bx1, by1, bx2, by2 = b[0], b[1], b[0] + b[2], b[1] + b[3]
                    s1 = (bx1 <= ax1 <= bx2) or (bx1 <= ax2 <= bx2)
                    s2 = (by1 <= ay1 <= by2) or (by1 <= ay2 <= by2)
                    s3 = (ax1 <= bx1 <= ax2) or (ax1 <= bx2 <= ax2)
                    s4 = (ay1 <= by1 <= ay2) or (ay1 <= by2 <= ay2)
                    if ((s1 and s2) or (s3 and s4)) or ((s1 and s4) or (s3 and s2)):
                        collides.append(self.level_elements[i][j])
        return collides

    def check_defeat(self):
        for _ in self.collide_with_player():
            if _[0] == 's':
                return True
        return False


def main():
    running = True
    screen = pygame.display.set_mode(SZ)
    pygame.display.set_caption("geometryDashPygame")
    clock = pygame.time.Clock()
    bg = load_image('bg.png')
    level = Level(screen, 'test_level.csv')
    screen.fill("white")
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                if not level.is_jumping_up and not level.is_jumping_down:
                    level.is_jumping_up = True
                    level.is_jumping = True
                    level.start_pos_jump = level.y
            if event.type == pygame.KEYUP and event.key == pygame.K_SPACE:
                level.is_jumping = False
        if level.is_jumping:
            if level.is_jumping_up:
                if not level.start_pos_jump - (level.size * 2.5) - 1 > level.y < level.start_pos_jump - \
                       (level.size * 2) + 1:
                    level.y -= V_Y / FPS
                else:
                    level.is_jumping_up = False
                    level.is_jumping_down = True
            elif level.is_jumping_down:
                platform_existing = False
                platform_y = None
                collides = level.collide_with_player()
                for _ in collides:
                    if _[0] == 'b' and _[1][1] - level.size <= level.y and (_[1][0] >= level.x or _[1][0] +
                                                                            level.size >= level.x):
                        platform_existing = True
                        platform_y = _[1][1]
                if not platform_existing:
                    level.y += V_Y / FPS
                else:
                    level.y = platform_y - level.size
                    level.start_pos_jump = level.y
                    level.is_jumping_up = True
                    level.is_jumping_down = False
        else:
            if level.is_jumping_up:
                if not level.start_pos_jump - (level.size * 2.5) - 1 > level.y < level.start_pos_jump - \
                       (level.size * 2) + 1:
                    level.y -= V_Y / FPS
                else:
                    level.is_jumping_up = False
                    level.is_jumping_down = True
            elif level.is_jumping_down:
                platform_existing = False
                platform_y = None
                collides = level.collide_with_player()
                for _ in collides:
                    if _[0] == 'b' and _[1][1] - level.size <= level.y and (_[1][0] >= level.x or _[1][0] +
                                                                            level.size >= level.x):
                        platform_existing = True
                        platform_y = _[1][1]
                if not platform_existing:
                    level.y += V_Y / FPS
                else:
                    level.y = platform_y - level.size
                    level.is_jumping_up = False
                    level.is_jumping_down = False
        if not level.collide_with_player() and not level.is_jumping_up and not level.is_jumping_down:
            level.is_jumping_down = True
        for spike in level.spikes:
            if pygame.sprite.collide_mask(level.player, spike):
                running = False
        screen.blit(bg, (0, 0))
        level.render()
        pygame.display.flip()
        level.delta += V_X / FPS
        clock.tick(FPS)


if __name__ == '__main__':
    main()