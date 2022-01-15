import pygame
import os
import sys
import csv
import tkinter
import tkinter.filedialog

SZ = (800, 700)
FPS = 180
A = (10 / (FPS / 120)) * (SZ[1] / 400)
JUMP_V = 300 * (SZ[1] / 400)
V_X = 200 * (SZ[1] / 400)
ANGLE_PER_SECOND = 360 / FPS


def load_image(name, color_key=None):
    fullname = os.path.join('resources', os.path.join('images', name))
    if not os.path.isfile(fullname):
        print(f"File with image '{fullname}' not found")
        sys.exit()
    image = pygame.image.load(fullname)
    return image


def load_skin(name, color_key=None):
    fullname = name
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


def cut_sheet(sheet, columns, rows):
    frames = []
    rect = pygame.Rect(0, 0, sheet.get_width() // columns, sheet.get_height() // rows)
    for j in range(rows):
        for i in range(columns):
            frame_location = (rect.w * i, rect.h * j)
            frames.append(sheet.subsurface(pygame.Rect(
                frame_location, rect.size)))
    return frames


def find_delta(changed_size, size):
    center = size / 2
    return center - (changed_size / 2)


def pause(screen, size, play_coords, menu_coords):
    surface = pygame.Surface(SZ)
    surface.set_alpha(128)
    surface.fill((0, 0, 0))
    screen.blit(surface, (0, 0))
    play_btn_image = pygame.transform.scale(load_image('play_btn.png'), (size, size))
    menu_btn_image = pygame.transform.scale(load_image('menu_btn.png'), (size, size))
    screen.blit(play_btn_image, play_coords)
    screen.blit(menu_btn_image, menu_coords)


def prompt_file():
    top = tkinter.Tk()
    top.withdraw()
    file_name = tkinter.filedialog.askopenfilename(parent=top)
    top.destroy()
    return file_name


class Explosive(pygame.sprite.Sprite):
    def __init__(self, s, group, x, y, cur_frame, frames):
        super().__init__(group)
        self.image = frames[cur_frame % 48]
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = x - s, y - s


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


class Wrecked(pygame.sprite.Sprite):

    def __init__(self, group, coords, size, image=load_image("obj-breakable.png")):
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
        self.size = SZ[1] // 20
        self.angle = 0
        self.player_angle = 0
        self.player = None
        self.btn_size = SZ[0] / 3
        self.play_btn_coords = SZ[0] / 2 - (self.btn_size * 1.25), SZ[1] / 2 - (self.btn_size * 0.5)
        self.menu_btn_coords = SZ[0] / 2 + (self.btn_size * 0.25), SZ[1] / 2 - (self.btn_size * 0.5)
        self.exp_frames = cut_sheet(sheet=pygame.transform.scale(load_image('explosive.png'),
                                                                 (self.size * 24, self.size * 18)), columns=8, rows=6)
        self.spikes = []
        self.orbs = []
        self.screen = screen
        self.is_jumping = False
        self.level_elements = []
        self.level = level_data(level)
        self.player_alpha = 0
        self.delta = 0
        self.y = self.find_spawn_point() * self.size
        self.x = self.size * 3
        self.player = Player(self.group, self.y, self.size, 0)
        self.player_image = self.player.image

    def render(self, c_o_f, explosive=False, e_o_f=0):
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

                if self.level[i][j] == 'w':
                    Wrecked(self.group, (self.size * j - self.delta, self.size * i), self.size)
                    self.level_elements[i].append(('w', (self.size * j - self.delta, self.size * i)))

                if self.level[i][j] == '0':
                    self.level_elements[i].append(None)

        if explosive:
            Explosive(self.size, self.group, self.x, self.y, e_o_f, self.exp_frames)

        self.group.draw(self.screen)

    def find_spawn_point(self):
        for i in range(len(self.level)):
            if self.level[i][3] != '0':
                return i - 1

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


def game(skin_path='bebra'):
    running = True
    screen = pygame.display.set_mode(SZ)
    pygame.display.set_caption("GeometryDashPygame")
    clock = pygame.time.Clock()
    while running:
        actual_try = True
        is_paused = False
        count_orb = 0
        count_exp = 0
        current_orb_frame = 0
        current_exp_frame = 0
        is_rotated = False
        level = Level(screen, 'test_level.csv')
        dead = False
        global_jumping = False
        explosive = False
        bg = load_image('bg.png')
        bg = pygame.transform.scale(bg, SZ).convert_alpha()
        while actual_try:
            collides = level.collide_with_player()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    actual_try = False
                    running = False

                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    on_orb = False
                    for sprite in pygame.sprite.spritecollide(level.player, level.group, False):
                        if isinstance(sprite, Orb):
                            on_orb = True

                    if not level.is_jumping or on_orb:
                        global_jumping = True
                        level.is_jumping = True
                        level.v_y = JUMP_V

                    if level.v_y < 0:
                        global_jumping = True

                if event.type == pygame.KEYUP and event.key == pygame.K_SPACE:
                    global_jumping = False

                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    if is_paused:
                        is_paused = False
                    else:
                        is_paused = True
                        pause(screen, level.btn_size, level.play_btn_coords, level.menu_btn_coords)

                if is_paused and event.type == pygame.MOUSEBUTTONDOWN:
                    pos = event.pos

                    if pos[0] in range(round(level.play_btn_coords[0]), round(level.play_btn_coords[0] +
                                                                              level.btn_size)):

                        if pos[1] in range(round(level.play_btn_coords[1]), round(level.play_btn_coords[1] +
                                                                                  level.btn_size)):
                            is_paused = False

                    if pos[0] in range(round(level.menu_btn_coords[0]), round(level.menu_btn_coords[0] +
                                                                              level.btn_size)):

                        if pos[1] in range(round(level.menu_btn_coords[1]), round(level.menu_btn_coords[1] +
                                                                                  level.btn_size)):
                            actual_try = False
                            running = False

            if not is_paused:

                screen.fill("white")

                if level.is_jumping and not dead:
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
                        if not _[1][1] + level.size * 0.75 < level.y:
                            dead = True

                    if _[0] == 'b' and _[1][1] - level.size <= level.y and \
                            (_[1][0] >= level.x or _[1][0] + level.size >= level.x):
                        if not _[1][1] + level.size * 0.75 < level.y and not dead:
                            level.v_y = 0
                            level.y = _[1][1] - level.size
                            level.is_jumping = False

                if not collides:
                    level.is_jumping = True

                if global_jumping and not level.is_jumping:
                    level.is_jumping = True
                    level.v_y = JUMP_V

                if level.y < level.size * -40 or level.y > level.size * 40:
                    dead = True

                for spike in level.spikes:
                    if pygame.sprite.collide_mask(level.player, spike):
                        dead = True

                if count_orb % (FPS * 0.3) == 0:
                    current_orb_frame += 1

                if not dead:
                    level.delta += V_X / FPS
                else:
                    level.player_alpha = 0
                    explosive = True
                    count_exp += 1
                    if count_exp % (FPS // 48) == 0:
                        current_exp_frame += 1
                    if current_exp_frame == 48:
                        actual_try = False

                screen.blit(bg, (0, 0))
                level.render(current_orb_frame % 3, explosive, current_exp_frame)

                if level.player_alpha == 0 and not dead:
                    image = pygame.transform.scale(load_image('avatar.png'), (level.size, level.size)).convert_alpha()
                    image = pygame.transform.rotate(image, level.angle)
                    delt = find_delta(image.get_size()[0], level.size)
                    screen.blit(image, (level.x + delt, level.y + delt))

                elif not is_rotated and not dead:
                    level.angle = 90 * (round(level.angle / 90))
                    level.player_image = pygame.transform.rotate(level.player_image, level.angle - level.player_angle)
                    level.player_angle = level.angle
                    is_rotated = True
                    if dead:
                        level.alpha = 0

                count_orb += 1

            pygame.display.flip()
            clock.tick(FPS)


if __name__ == '__main__':
    game()
