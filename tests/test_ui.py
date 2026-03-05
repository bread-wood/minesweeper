import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pytest
import pygame

from game.board import Board, WON, LOST
from ui.renderer import Renderer, CELL_SIZE, MARGIN, HEADER_HEIGHT


@pytest.fixture(autouse=True)
def pygame_session():
    pygame.init()
    yield
    pygame.quit()


@pytest.fixture
def board():
    return Board(seed=42)


@pytest.fixture
def renderer(board):
    return Renderer(board)


# --- Renderer initialisation ---


def test_renderer_dimensions(renderer, board):
    expected_w = board.cols * (CELL_SIZE + MARGIN) + MARGIN
    expected_h = board.rows * (CELL_SIZE + MARGIN) + MARGIN + HEADER_HEIGHT
    assert renderer.width == expected_w
    assert renderer.height == expected_h


def test_renderer_screen_size(renderer):
    w, h = renderer.screen.get_size()
    assert w == renderer.width
    assert h == renderer.height


# --- cell_at ---


def test_cell_at_header_returns_none(renderer):
    assert renderer.cell_at(100, HEADER_HEIGHT - 1) is None


def test_cell_at_top_left_cell(renderer):
    x = MARGIN + 1
    y = HEADER_HEIGHT + MARGIN + 1
    result = renderer.cell_at(x, y)
    assert result == (0, 0)


def test_cell_at_second_row(renderer):
    x = MARGIN + 1
    y = HEADER_HEIGHT + MARGIN + CELL_SIZE + MARGIN + 1
    result = renderer.cell_at(x, y)
    assert result == (1, 0)


def test_cell_at_second_col(renderer):
    x = MARGIN + CELL_SIZE + MARGIN + 1
    y = HEADER_HEIGHT + MARGIN + 1
    result = renderer.cell_at(x, y)
    assert result == (0, 1)


def test_cell_at_negative_coords(renderer):
    assert renderer.cell_at(-10, -10) is None


def test_cell_at_far_outside(renderer, board):
    assert renderer.cell_at(board.cols * 100, board.rows * 100) is None


# --- draw: smoke tests (just ensure no exception) ---


def test_draw_initial_state(renderer):
    renderer.draw()


def test_draw_after_safe_reveal(renderer, board):
    for r in range(board.rows):
        for c in range(board.cols):
            if not board.cells[r][c]["mine"]:
                board.reveal(r, c)
                break
    renderer.draw()


def test_draw_after_flag(renderer, board):
    board.flag(0, 0)
    renderer.draw()


def test_draw_after_unflag(renderer, board):
    board.flag(0, 0)
    board.flag(0, 0)
    renderer.draw()


def test_draw_game_lost(renderer, board):
    for r in range(board.rows):
        for c in range(board.cols):
            if board.cells[r][c]["mine"]:
                board.reveal(r, c)
                break
    assert board.state == LOST
    renderer.draw()


def test_draw_game_won(renderer, board):
    for r in range(board.rows):
        for c in range(board.cols):
            if not board.cells[r][c]["mine"]:
                board.cells[r][c]["state"] = "revealed"
    board.state = WON
    renderer.draw()


def test_draw_numbered_cell(renderer, board):
    # Reveal a cell that has adjacent mines (adjacent > 0)
    for r in range(board.rows):
        for c in range(board.cols):
            if not board.cells[r][c]["mine"] and board.cells[r][c]["adjacent"] > 0:
                board.cells[r][c]["state"] = "revealed"
                renderer.draw()
                return
    pytest.skip("No numbered cell found with this seed")


# --- board swap (main.py restart pattern) ---


def test_renderer_board_swap(renderer):
    new_board = Board(seed=99)
    renderer.board = new_board
    renderer.draw()
    assert renderer.board is new_board


# --- game integration: flood fill propagates ---


def test_flood_fill_reveals_multiple_cells():
    board = Board(seed=42)
    initial_revealed = sum(
        1 for r in range(board.rows) for c in range(board.cols)
        if board.cells[r][c]["state"] == "revealed"
    )
    # Find a cell with 0 adjacent mines that isn't a mine
    for r in range(board.rows):
        for c in range(board.cols):
            if not board.cells[r][c]["mine"] and board.cells[r][c]["adjacent"] == 0:
                board.reveal(r, c)
                after_revealed = sum(
                    1 for rr in range(board.rows) for cc in range(board.cols)
                    if board.cells[rr][cc]["state"] == "revealed"
                )
                assert after_revealed > initial_revealed + 1
                return
    pytest.skip("No empty cell found with this seed")
