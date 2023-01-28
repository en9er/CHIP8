import sys

from CHIP8 import CHIP8
import pygame

WHITE = [255, 255, 255]
BLACK = [0, 0, 0]


def main_loop():
    size = 20
    clock = pygame.time.Clock()
    cpu = CHIP8()
    try:
        filename = sys.argv[1]
    except IndexError:
        print("Error: enter program filename to load")
        sys.exit()
    # cpu.load_program("./programs/demo/Breakout.ch8")
    # cpu.load_program("./programs/demo/Chip8_Logo.ch8")
    # cpu.load_program("./programs/demo/Chip8_Picture.ch8")
    # cpu.load_program("./programs/demo/Clock.ch8")
    # cpu.load_program("./programs/demo/IBMLogo.ch8")
    # cpu.load_program("./programs/demo/Zero_Demo.ch8")
    cpu.load_program("./programs/games/Space_Flight.ch8")
    screen = pygame.display.set_mode([cpu.screen_width * size, cpu.screen_height * size])
    pygame.time.set_timer(pygame.USEREVENT + 1, int(1000 / 60))
    while True:
        clock.tick(300)
        cpu.key_input()
        cpu.execute()
        cpu.decrement_timers()
        display(screen, cpu.screen_matrix)


def display(screen, screen_matrix):
    size = 20
    for i in range(0, len(screen_matrix)):
        for j in range(0, len(screen_matrix[0])):
            cellColor = BLACK

            if screen_matrix[i][j] == 1:
                cellColor = WHITE

            pygame.draw.rect(screen, cellColor, [j * size, i * size, size, size], 0)

    pygame.display.flip()


if __name__ == "__main__":
    main_loop()
