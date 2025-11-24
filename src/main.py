import pygame
import random
pygame.init()

screen_width, screen_height = 1440, 810
screen = pygame.display.set_mode((screen_width, screen_height))

bsize = 256
bcenter =(screen_width//2, screen_height//2)
scaled_image = pygame.transform.scale( pygame.image.load('pic/whiteball.png'), (bsize , bsize ))
image_rect = scaled_image.get_rect(center = bcenter)
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    screen.fill( (0,0,0) )
    image_rect.x += random.randint(-5, 5)
    image_rect.y += random.randint(-5, 5)
    screen.blit(scaled_image, image_rect)
    pygame.display.flip()

pygame.quit()