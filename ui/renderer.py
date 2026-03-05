import pygame

CELL_SIZE = 40
MARGIN = 2
HEADER_HEIGHT = 60

NUMBER_COLORS = {
    1: (0, 0, 255),
    2: (0, 128, 0),
    3: (255, 0, 0),
    4: (0, 0, 128),
    5: (128, 0, 0),
    6: (0, 128, 128),
    7: (0, 0, 0),
    8: (128, 128, 128),
}

COLOR_BG = (192, 192, 192)
COLOR_HIDDEN = (160, 160, 160)
COLOR_REVEALED = (220, 220, 220)
COLOR_MINE = (200, 0, 0)
COLOR_FLAG = (255, 140, 0)
COLOR_TEXT = (0, 0, 0)
COLOR_WIN = (0, 180, 0)
COLOR_LOSE = (200, 0, 0)
COLOR_BORDER_LIGHT = (255, 255, 255)
COLOR_BORDER_DARK = (100, 100, 100)


class Renderer:
    def __init__(self, board):
        self.board = board
        self.width = board.cols * (CELL_SIZE + MARGIN) + MARGIN
        self.height = board.rows * (CELL_SIZE + MARGIN) + MARGIN + HEADER_HEIGHT
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Minesweeper")
        self.font = pygame.font.SysFont("monospace", 22, bold=True)
        self.header_font = pygame.font.SysFont("monospace", 20, bold=True)

    def draw(self):
        self.screen.fill(COLOR_BG)
        self._draw_header()
        self._draw_board()
        pygame.display.flip()

    def _draw_header(self):
        state = self.board.state
        if state == "won":
            text = "You Win! :)"
            color = COLOR_WIN
        elif state == "lost":
            text = "Game Over :("
            color = COLOR_LOSE
        else:
            flags = sum(
                1
                for r in range(self.board.rows)
                for c in range(self.board.cols)
                if self.board.cells[r][c]["state"] == "flagged"
            )
            text = f"Mines: {self.board.mines - flags}"
            color = COLOR_TEXT
        surf = self.header_font.render(text, True, color)
        rect = surf.get_rect(center=(self.width // 2, HEADER_HEIGHT // 2))
        self.screen.blit(surf, rect)

    def _draw_board(self):
        for r in range(self.board.rows):
            for c in range(self.board.cols):
                self._draw_cell(r, c)

    def _draw_cell(self, row: int, col: int):
        x = MARGIN + col * (CELL_SIZE + MARGIN)
        y = HEADER_HEIGHT + MARGIN + row * (CELL_SIZE + MARGIN)
        rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
        cell = self.board.cells[row][col]
        state = cell["state"]

        if state == "revealed":
            pygame.draw.rect(self.screen, COLOR_REVEALED, rect)
            pygame.draw.rect(self.screen, COLOR_BORDER_DARK, rect, 1)
            if cell["mine"]:
                pygame.draw.circle(self.screen, COLOR_MINE, rect.center, CELL_SIZE // 4)
            elif cell["adjacent"] > 0:
                color = NUMBER_COLORS.get(cell["adjacent"], COLOR_TEXT)
                surf = self.font.render(str(cell["adjacent"]), True, color)
                text_rect = surf.get_rect(center=rect.center)
                self.screen.blit(surf, text_rect)
        else:
            pygame.draw.rect(self.screen, COLOR_HIDDEN, rect)
            pygame.draw.line(self.screen, COLOR_BORDER_LIGHT, rect.topleft, rect.topright, 2)
            pygame.draw.line(self.screen, COLOR_BORDER_LIGHT, rect.topleft, rect.bottomleft, 2)
            pygame.draw.line(self.screen, COLOR_BORDER_DARK, rect.bottomleft, rect.bottomright, 2)
            pygame.draw.line(self.screen, COLOR_BORDER_DARK, rect.topright, rect.bottomright, 2)
            if state == "flagged":
                surf = self.font.render("F", True, COLOR_FLAG)
                text_rect = surf.get_rect(center=rect.center)
                self.screen.blit(surf, text_rect)

    def cell_at(self, x: int, y: int):
        """Convert pixel coordinates to (row, col), or None if outside the board."""
        if y < HEADER_HEIGHT:
            return None
        board_x = x - MARGIN
        board_y = y - HEADER_HEIGHT - MARGIN
        if board_x < 0 or board_y < 0:
            return None
        col = board_x // (CELL_SIZE + MARGIN)
        row = board_y // (CELL_SIZE + MARGIN)
        if 0 <= row < self.board.rows and 0 <= col < self.board.cols:
            return (row, col)
        return None
