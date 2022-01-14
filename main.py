import pygame
import os
import sys
import csv

SZ = (800, 700)
FPS = 300
A = (9.8 / (FPS / 120)) * (SZ[1] / 400)
JUMP_V = 300 * (SZ[1] / 400)
V_X = 200 * (SZ[1] / 400)
ANGLE_PER_SECOND = 360 / FPS


def load_image(name, color_key=None):
    fullname = os.path.join('images', name)
    if not os.path.isfile(fullname):
        print(f"File with image '{fullname}' not found")
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


def find_delta(changed_size, size):
    center = size / 2
    return center - (changed_size / 2)


class Block(pygame.sprite.Sprite):

    def __init__(self, group, coords, size, image=load_image("block_1.png")):
        super().__init__(group)
        image = pygame.transform.scale(image, (size, size))
        image.set_alpha(256)
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = coords


class Spike(pygame.sprite.Sprite):

    def __init__(self, group, coords, size, image=load_image("obj-spike.png")):
        super().__init__(group)
        image = pygame.transform.scale(image, (size, size)).convert_alpha()
        image.set_alpha(256)
        self.mask = pygame.mask.from_surface(image)
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = coords


class Player(pygame.sprite.Sprite):

    def __init__(self, group, coords, size, alpha=256, image=load_image('avatar.png')):
        super().__init__(group)
        image = pygame.transform.scale(image, (size, size)).convert_alpha()
        image.set_alpha(alpha)
        self.image = image
        self.mask = pygame.mask.from_surface(image)
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = size * 3, coords


class Orb(pygame.sprite.Sprite):

    frames = ['orb-yellow1.png', 'orb-yellow2.png', 'orb-yellow.png']

    def __init__(self, group, coords, size, alpha=256, current_frame=0):
        super().__init__(group)
        image = pygame.transform.scale(load_image(Orb.frames[current_frame]), (size, size)).convert_alpha()
        image.set_alpha(alpha)
        self.image = image
        self.mask = pygame.mask.from_surface(image)
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = coords


class Level:

    def __init__(self, screen, level):
        self.group = pygame.sprite.Group()
        self.v_y = 0
        self.a = A / FPS
        self.angle = 0
        self.player_angle = 0
        self.player = None
        self.spikes = []
        self.orbs = []
        self.screen = screen
        self.is_jumping = False
        self.level_elements = []
        self.level = level_data(level)
        self.player_alpha = 0
        self.delta = 0
        self.size = SZ[1] // 20
        self.y = self.find_spawn_point() * self.size
        self.x = self.size * 3
        self.player = Player(self.group, self.y, self.size, 0)
        self.player_image = self.player.image

    def render(self, c_o_f):
        self.spikes = []
        self.orbs = []
        self.group = pygame.sprite.Group()
        self.player = Player(self.group, self.y, self.size, self.player_alpha, self.player_image)
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

                if self.level[i][j] == 'o':
                    orb = Orb(self.group, (self.size * j - self.delta, self.size * i), self.size, current_frame=c_o_f)
                    self.level_elements[i].append(('o', (self.size * j - self.delta, self.size * i)))
                    self.orbs.append(orb)

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


def main():
    running = True
    screen = pygame.display.set_mode(SZ)
    count_orb = 0
    current_orb_frame = 0
    is_rotated = False
    level = Level(screen, 'test_level1.csv')
    pygame.display.set_caption("geometryDashPygame")
    clock = pygame.time.Clock()
    global_jumping = False
    bg = load_image('bg.png')
    bg = pygame.transform.scale(bg, SZ).convert_alpha()
    screen.fill("white")
    while running:
        collides = level.collide_with_player()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE or event.type == pygame.MOUSEBUTTONDOWN:
                on_orb = False
                for orb in level.orbs:
                    if pygame.sprite.collide_mask(level.player, orb):
                        on_orb = True
                if not level.is_jumping or on_orb:
                    global_jumping = True
                    level.is_jumping = True
                    level.v_y = JUMP_V

                if level.v_y < 0:
                    global_jumping = True

            if event.type == pygame.KEYUP and event.key == pygame.K_SPACE or event.type == pygame.MOUSEBUTTONUP:
                global_jumping = False

        if level.is_jumping:
            level.y -= level.v_y / FPS
            level.v_y -= A
            is_rotated = False
            level.player_alpha = 0
        else:
            level.player_alpha = 256

        if level.player_alpha == 0:
            level.angle -= ANGLE_PER_SECOND

        for _ in collides:
            if _[0] == 'b' and level.y + level.size * 0.75 >= _[1][1]:
                running = False

            if _[0] == 'b' and _[1][1] - level.size <= level.y and \
                    (_[1][0] >= level.x or _[1][0] + level.size >= level.x):
                level.v_y = 0
                level.y = _[1][1] - level.size
                level.is_jumping = False
        if not collides:
            level.is_jumping = True

        if global_jumping and not level.is_jumping:
            level.is_jumping = True
            level.v_y = JUMP_V

        if level.y < level.size * -40 or level.y > level.size * 40:
            running = False

        for spike in level.spikes:
            if pygame.sprite.collide_mask(level.player, spike):
                running = False

        if count_orb % (FPS * 0.3) == 0:
            current_orb_frame += 1

        screen.blit(bg, (0, 0))
        level.render(current_orb_frame % 3)

        if level.player_alpha == 0:
            image = pygame.transform.scale(load_image('avatar.png'), (level.size, level.size)).convert_alpha()
            image = pygame.transform.rotate(image, level.angle)
            delt = find_delta(image.get_size()[0], level.size)
            screen.blit(image, (level.x + delt, level.y + delt))

        elif not is_rotated:
            level.angle = 90 * (round(level.angle / 90))
            level.player_image = pygame.transform.rotate(level.player_image, level.angle - level.player_angle)
            level.player_angle = level.angle
            is_rotated = True

        pygame.display.flip()
        count_orb += 1
        level.delta += V_X / FPS
        clock.tick(FPS)


if __name__ == '__main__':
    main()
