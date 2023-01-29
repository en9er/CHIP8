import sys

import pygame

from CHIP8 import CHIP8

WHITE = [255, 255, 255]
BLACK = [0, 0, 0]
SIZE = 20


def main_loop():
    clock = pygame.time.Clock()
    cpu = CHIP8()
    try:
        filename = sys.argv[1]
        cpu.load_program(filename)
    except IndexError:
        print("Error: enter program filename to load")
        sys.exit()
    screen = pygame.display.set_mode(
        [cpu.screen_width * SIZE, cpu.screen_height * SIZE]
    )
    pygame.init()
    pygame.time.set_timer(pygame.USEREVENT + 1, 1)
    while True:
        clock.tick(200)
        cpu.key_input()
        cpu.execute()
        cpu.decrement_timers()
        display(screen, cpu.screen_matrix)


def display(screen, screen_matrix):
    for i in range(0, len(screen_matrix)):
        for j in range(0, len(screen_matrix[0])):
            pixel_color = BLACK
            if screen_matrix[i][j] == 1:
                pixel_color = WHITE

            pygame.draw.rect(screen, pixel_color, [j * SIZE, i * SIZE, SIZE, SIZE], 0)

    pygame.display.flip()


if __name__ == "__main__":
    main_loop()
