"""Tests for the minesweeper board."""

import pytest

from game.board import Board, CellState, GameState


# ---------------------------------------------------------------------------
# Board construction
# ---------------------------------------------------------------------------


class TestBoardConstruction:
    def test_basic_dimensions(self):
        board = Board(5, 10, 3)
        assert board.rows == 5
        assert board.cols == 10
        assert board.num_mines == 3

    def test_cells_count(self):
        board = Board(4, 4, 2)
        assert sum(1 for _ in board.cells()) == 16

    def test_invalid_dimensions(self):
        with pytest.raises(ValueError):
            Board(0, 5, 1)
        with pytest.raises(ValueError):
            Board(5, 0, 1)

    def test_negative_mines(self):
        with pytest.raises(ValueError):
            Board(5, 5, -1)

    def test_too_many_mines(self):
        with pytest.raises(ValueError):
            Board(3, 3, 9)  # must be < 9

    def test_initial_state_hidden(self):
        board = Board(3, 3, 1)
        for cell in board.cells():
            assert cell.state is CellState.HIDDEN

    def test_initial_game_state(self):
        board = Board(5, 5, 5)
        assert board.game_state is GameState.ONGOING


# ---------------------------------------------------------------------------
# Neighbor graph
# ---------------------------------------------------------------------------


class TestNeighborGraph:
    def test_corner_cell_has_three_neighbors(self):
        board = Board(5, 5, 1)
        assert len(board.cell(0, 0).neighbors) == 3

    def test_edge_cell_has_five_neighbors(self):
        board = Board(5, 5, 1)
        assert len(board.cell(0, 2).neighbors) == 5

    def test_inner_cell_has_eight_neighbors(self):
        board = Board(5, 5, 1)
        assert len(board.cell(2, 2).neighbors) == 8

    def test_neighbors_are_adjacent(self):
        board = Board(5, 5, 1)
        cell = board.cell(2, 2)
        for neighbor in cell.neighbors:
            assert abs(neighbor.row - 2) <= 1
            assert abs(neighbor.col - 2) <= 1
            assert not (neighbor.row == 2 and neighbor.col == 2)

    def test_1x1_board_no_neighbors(self):
        board = Board(1, 1, 0)
        assert board.cell(0, 0).neighbors == []


# ---------------------------------------------------------------------------
# Reveal mechanics
# ---------------------------------------------------------------------------


class TestReveal:
    def test_reveal_returns_ongoing_on_safe(self):
        board = Board(5, 5, 1)
        state = board.reveal(2, 2)
        assert state in (GameState.ONGOING, GameState.WON)

    def test_first_reveal_not_mine(self):
        """After any first reveal the chosen cell must be safe."""
        for _ in range(20):
            board = Board(4, 4, 12)  # lots of mines
            state = board.reveal(0, 0)
            assert state is not GameState.LOST
            assert board.cell(0, 0).state is CellState.REVEALED

    def test_reveal_hidden_cell_changes_state(self):
        board = Board(5, 5, 1)
        board.reveal(2, 2)
        assert board.cell(2, 2).state is CellState.REVEALED

    def test_reveal_flagged_cell_does_nothing(self):
        board = Board(5, 5, 1)
        board.flag(2, 2)
        board.reveal(2, 2)
        assert board.cell(2, 2).state is CellState.FLAGGED

    def test_reveal_already_revealed_cell_noop(self):
        board = Board(5, 5, 1)
        board.reveal(2, 2)
        state_before = board.game_state
        board.reveal(2, 2)
        assert board.game_state is state_before

    def test_out_of_bounds_raises(self):
        board = Board(5, 5, 1)
        with pytest.raises(IndexError):
            board.reveal(10, 0)
        with pytest.raises(IndexError):
            board.reveal(0, -1)

    def test_no_actions_after_loss(self):
        board = _force_loss(Board(5, 5, 5))
        assert board.game_state is GameState.LOST
        state = board.reveal(0, 0)
        assert state is GameState.LOST

    def test_flood_fill_reveals_empty_region(self):
        """A zero-mine board should reveal every cell on first reveal."""
        board = Board(4, 4, 0)
        board.reveal(0, 0)
        for cell in board.cells():
            assert cell.state is CellState.REVEALED

    def test_win_condition(self):
        """A zero-mine board wins immediately after revealing all cells."""
        board = Board(3, 3, 0)
        state = board.reveal(0, 0)
        assert state is GameState.WON


# ---------------------------------------------------------------------------
# Flagging
# ---------------------------------------------------------------------------


class TestFlag:
    def test_flag_hidden_cell(self):
        board = Board(5, 5, 3)
        board.flag(0, 0)
        assert board.cell(0, 0).state is CellState.FLAGGED

    def test_unflag_flagged_cell(self):
        board = Board(5, 5, 3)
        board.flag(0, 0)
        board.flag(0, 0)
        assert board.cell(0, 0).state is CellState.HIDDEN

    def test_cannot_flag_revealed_cell(self):
        board = Board(5, 5, 1)
        board.reveal(2, 2)
        board.flag(2, 2)
        assert board.cell(2, 2).state is CellState.REVEALED

    def test_remaining_mines_decrements(self):
        board = Board(5, 5, 3)
        assert board.remaining_mines() == 3
        board.flag(0, 0)
        assert board.remaining_mines() == 2
        board.flag(0, 1)
        assert board.remaining_mines() == 1

    def test_remaining_mines_increments_on_unflag(self):
        board = Board(5, 5, 3)
        board.flag(0, 0)
        board.flag(0, 0)
        assert board.remaining_mines() == 3


# ---------------------------------------------------------------------------
# Mine placement (deterministic helpers)
# ---------------------------------------------------------------------------


class TestMinePlacement:
    def test_mine_count_correct(self):
        board = Board(10, 10, 15)
        board.reveal(0, 0)  # triggers placement
        mine_count = sum(1 for c in board.cells() if c.is_mine)
        assert mine_count == 15

    def test_first_reveal_cell_is_never_mine(self):
        for _ in range(30):
            board = Board(5, 5, 20)
            board.reveal(2, 2)
            assert not board.cell(2, 2).is_mine

    def test_adjacent_mine_counts_are_accurate(self):
        board = Board(5, 5, 5)
        board.reveal(0, 0)
        for cell in board.cells():
            expected = sum(1 for n in cell.neighbors if n.is_mine)
            assert cell.adjacent_mines == expected


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _force_loss(board: Board) -> Board:
    """Reveal cells until a mine is hit or all safe cells are clear."""
    board.reveal(0, 0)  # safe first move
    for cell in board.cells():
        if cell.is_mine:
            # Directly set state to simulate hitting a mine (bypassing first-reveal guard)
            cell.state = CellState.REVEALED
            board.game_state = GameState.LOST
            return board
    return board
