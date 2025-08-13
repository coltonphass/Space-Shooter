import pygame
from random import randint, uniform
from os.path import join
import sys, os

# ----------------- HELPER -----------------
def resource_path(relative_path):
    """ Get the path to the resource, works for dev and PyInstaller """
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


# ----------------- CLASSES -----------------
class Player(pygame.sprite.Sprite):
    def __init__(self, groups, laser_surface, laser_sprites, laser_sound):
        super().__init__(groups)
        self.image = pygame.image.load(resource_path('images/player.png')).convert_alpha()
        self.rect = self.image.get_frect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2))
        self.direction = pygame.math.Vector2()
        self.speed = 300

        self.can_shoot = True
        self.laser_shoot_time = 0
        self.cooldown_duration = 400
        self.mask = pygame.mask.from_surface(self.image)

        self.laser_surface = laser_surface
        self.laser_sprites = laser_sprites
        self.laser_sound = laser_sound
        self.all_sprites = groups[0]

    def laser_timer(self):
        if not self.can_shoot:
            current_time = pygame.time.get_ticks()
            if current_time - self.laser_shoot_time >= self.cooldown_duration:
                self.can_shoot = True

    def update(self, dt):
        keys = pygame.key.get_pressed()
        self.direction.x = int(keys[pygame.K_RIGHT] or keys[pygame.K_d]) - int(keys[pygame.K_LEFT] or keys[pygame.K_a])
        self.direction.y = int(keys[pygame.K_DOWN] or keys[pygame.K_s]) - int(keys[pygame.K_UP] or keys[pygame.K_w])
        self.direction = self.direction.normalize() if self.direction else self.direction
        self.rect.center += self.direction * self.speed * dt


        # Boundary check
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > WINDOW_WIDTH:
            self.rect.right = WINDOW_WIDTH

        if self.rect.bottom > WINDOW_HEIGHT:
            self.rect.bottom = WINDOW_HEIGHT

        if self.rect.top < 0:
            self.rect.top = 0


        recent_keys = pygame.key.get_just_pressed()
        if recent_keys[pygame.K_SPACE] and self.can_shoot:
            Laser(self.laser_surface, self.rect.midtop, (self.all_sprites, self.laser_sprites))
            self.can_shoot = False
            self.laser_shoot_time = pygame.time.get_ticks()
            self.laser_sound.play()

        self.laser_timer()


class Star(pygame.sprite.Sprite):
    def __init__(self, groups, surf):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_frect(center=(randint(0, WINDOW_WIDTH), randint(0, WINDOW_HEIGHT)))


class Laser(pygame.sprite.Sprite):
    def __init__(self, surf, pos, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_frect(midbottom=pos)

    def update(self, dt):
        self.rect.centery -= 400 * dt
        if self.rect.bottom < 0:
            self.kill()


class Meteor(pygame.sprite.Sprite):
    def __init__(self, surf, pos, groups):
        super().__init__(groups)
        self.original_surface = surf
        self.image = surf
        self.rect = self.image.get_frect(center=pos)
        self.spawn_time = pygame.time.get_ticks()
        self.lifetime = 3000
        self.direction = pygame.Vector2(uniform(-0.5, 0.5), 1)
        self.speed = randint(400, 500)
        self.rotation_speed = randint(40, 80)
        self.rotation = 0

    def update(self, dt):
        self.rect.center += self.direction * self.speed * dt
        current_time = pygame.time.get_ticks()
        if current_time - self.spawn_time >= self.lifetime:
            self.kill()

        self.rotation += self.rotation_speed * dt
        self.image = pygame.transform.rotozoom(self.original_surface, self.rotation, 1)
        self.rect = self.image.get_frect(center=self.rect.center)


class AnimatedExplosion(pygame.sprite.Sprite):
    def __init__(self, frames, pos, groups):
        super().__init__(groups)
        self.frames = frames
        self.frame_index = 0
        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_frect(center=pos)

    def update(self, dt):
        self.frame_index += 20 * dt
        if self.frame_index < len(self.frames):
            self.image = self.frames[int(self.frame_index)]
        else:
            self.kill()


# ----------------- FUNCTIONS -----------------
def collisions(player, meteor_sprites, laser_sprites, explosion_frames, explosion_sound, all_sprites):
    player_collision = pygame.sprite.spritecollide(player, meteor_sprites, True, pygame.sprite.collide_mask)
    if player_collision:
        return True  # game over

    for laser in laser_sprites:
        laser_collision = pygame.sprite.spritecollide(laser, meteor_sprites, True)
        if laser_collision:
            laser.kill()
            AnimatedExplosion(explosion_frames, laser.rect.midtop, all_sprites)
            explosion_sound.play()
    return False


def display_score(start_time, font, display_surface):
    elapsed_time = (pygame.time.get_ticks() - start_time) // 100
    text_surface = font.render(str(elapsed_time), True, (240, 240, 240))
    text_rect = text_surface.get_frect(midbottom=(WINDOW_WIDTH / 2, WINDOW_HEIGHT - 50))
    display_surface.blit(text_surface, text_rect)
    pygame.draw.rect(display_surface, (240, 240, 240), text_rect.inflate(20, 10).move(0, -8), 5, 10)


def game_over_screen(font, display_surface):
    text_surface = font.render('Game Over', True, (255, 255, 255))
    text_rect = text_surface.get_frect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2))
    display_surface.blit(text_surface, text_rect)

    restart_surface = font.render('Press R to Restart or Q to Quit', True, (200, 200, 200))
    restart_rect = restart_surface.get_frect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 + 50))
    display_surface.blit(restart_surface, restart_rect)

    pygame.display.update()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    sys.exit()
                elif event.key == pygame.K_r:
                    return  # restart


def run_game():
    # Sprite groups
    all_sprites = pygame.sprite.Group()
    meteor_sprites = pygame.sprite.Group()
    laser_sprites = pygame.sprite.Group()

    # Stars
    for _ in range(20):
        Star(all_sprites, star_surf)

    # Player
    player = Player((all_sprites,), laser_surface, laser_sprites, laser_sound)

    # Timer
    pygame.time.set_timer(meteor_event, 300)

    start_time = pygame.time.get_ticks()
    clock = pygame.time.Clock()
    running = True

    while running:
        dt = clock.tick() / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == meteor_event:
                x, y = randint(0, WINDOW_WIDTH), randint(-200, -100)
                Meteor(meteor_surface, (x, y), (all_sprites, meteor_sprites))

        # Update
        all_sprites.update(dt)
        if collisions(player, meteor_sprites, laser_sprites, explosion_frames, explosion_sound, all_sprites):
            running = False

        # Draw
        display_surface.fill('#3a2e3f')
        all_sprites.draw(display_surface)
        display_score(start_time, font, display_surface)
        pygame.display.update()


# ----------------- SETUP -----------------
pygame.init()
WINDOW_WIDTH, WINDOW_HEIGHT = 1280, 720
display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption('Space shooter')

# Assets
star_surf = pygame.image.load(resource_path('images/star.png')).convert_alpha()
meteor_surface = pygame.image.load(resource_path('images/meteor.png')).convert_alpha()
laser_surface = pygame.image.load(resource_path('images/laser.png')).convert_alpha()
font = pygame.font.Font(resource_path('images/Oxanium-Bold.ttf'), 40)
explosion_frames = [pygame.image.load(resource_path(f'images/explosion/{i}.png')).convert_alpha() for i in range(21)]

laser_sound = pygame.mixer.Sound(resource_path('audio/laser.wav'))
laser_sound.set_volume(0.04)
explosion_sound = pygame.mixer.Sound(resource_path('audio/explosion.wav'))
explosion_sound.set_volume(0.05)
game_music = pygame.mixer.Sound(resource_path('audio/game_music.wav'))
game_music.set_volume(0.03)
game_music.play(loops=-1)

meteor_event = pygame.event.custom_type()

# ----------------- MAIN LOOP -----------------
while True:
    run_game()
    game_over_screen(font, display_surface)
