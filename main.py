import sys

import pygame

from game.board import Board
from ui.renderer import Renderer


def main():
    pygame.init()
    board = Board()
    renderer = Renderer(board)
    clock = pygame.time.Clock()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = renderer.cell_at(*event.pos)
                if pos:
                    row, col = pos
                    if event.button == 1:
                        board.reveal(row, col)
                    elif event.button == 3:
                        board.flag(row, col)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    board = Board()
                    renderer.board = board

        renderer.draw()
        clock.tick(30)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
