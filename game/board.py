"""Minesweeper board implemented as a graph of cells."""

from __future__ import annotations

import random
from enum import Enum, auto
from typing import Iterable, List, Set, Tuple


class CellState(Enum):
    HIDDEN = auto()
    REVEALED = auto()
    FLAGGED = auto()


class GameState(Enum):
    ONGOING = auto()
    WON = auto()
    LOST = auto()


class Cell:
    """A single cell in the minesweeper board graph."""

    def __init__(self, row: int, col: int) -> None:
        self.row = row
        self.col = col
        self.is_mine: bool = False
        self.adjacent_mines: int = 0
        self.state: CellState = CellState.HIDDEN
        self.neighbors: List["Cell"] = []

    def __repr__(self) -> str:
        return f"Cell({self.row}, {self.col})"


class Board:
    """
    Minesweeper board modelled as a graph.

    Each cell is a node; edges connect all 8-directional neighbors.
    Mine placement happens after the first reveal to guarantee the first
    move is always safe.
    """

    def __init__(self, rows: int, cols: int, num_mines: int) -> None:
        if rows < 1 or cols < 1:
            raise ValueError("Board dimensions must be positive")
        if num_mines < 0:
            raise ValueError("num_mines cannot be negative")
        if num_mines >= rows * cols:
            raise ValueError("num_mines must be less than total cells")

        self.rows = rows
        self.cols = cols
        self.num_mines = num_mines
        self.game_state = GameState.ONGOING
        self._mines_placed = False

        # Build grid
        self._grid: List[List[Cell]] = [
            [Cell(r, c) for c in range(cols)] for r in range(rows)
        ]

        # Wire up neighbor graph
        for r in range(rows):
            for c in range(cols):
                self._grid[r][c].neighbors = self._compute_neighbors(r, c)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def reveal(self, row: int, col: int) -> GameState:
        """Reveal a cell. Returns the current GameState."""
        self._validate(row, col)
        if self.game_state is not GameState.ONGOING:
            return self.game_state

        cell = self._grid[row][col]
        if cell.state is CellState.FLAGGED:
            return self.game_state
        if cell.state is CellState.REVEALED:
            return self.game_state

        # Place mines on first reveal, excluding the chosen cell
        if not self._mines_placed:
            self._place_mines(exclude=(row, col))

        if cell.is_mine:
            cell.state = CellState.REVEALED
            self.game_state = GameState.LOST
            return self.game_state

        self._flood_reveal(cell)
        self._check_win()
        return self.game_state

    def flag(self, row: int, col: int) -> None:
        """Toggle a flag on a hidden cell."""
        self._validate(row, col)
        if self.game_state is not GameState.ONGOING:
            return
        cell = self._grid[row][col]
        if cell.state is CellState.HIDDEN:
            cell.state = CellState.FLAGGED
        elif cell.state is CellState.FLAGGED:
            cell.state = CellState.HIDDEN

    def cell(self, row: int, col: int) -> Cell:
        """Return the Cell at (row, col)."""
        self._validate(row, col)
        return self._grid[row][col]

    def cells(self) -> Iterable[Cell]:
        """Iterate over all cells in row-major order."""
        for row in self._grid:
            yield from row

    def remaining_mines(self) -> int:
        """Mines minus flagged cells (can go negative if over-flagged)."""
        flagged = sum(1 for c in self.cells() if c.state is CellState.FLAGGED)
        return self.num_mines - flagged

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _validate(self, row: int, col: int) -> None:
        if not (0 <= row < self.rows and 0 <= col < self.cols):
            raise IndexError(f"({row}, {col}) out of bounds for {self.rows}x{self.cols} board")

    def _compute_neighbors(self, row: int, col: int) -> List[Cell]:
        neighbors: List[Cell] = []
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                r, c = row + dr, col + dc
                if 0 <= r < self.rows and 0 <= c < self.cols:
                    neighbors.append(self._grid[r][c])
        return neighbors

    def _place_mines(self, exclude: Tuple[int, int]) -> None:
        all_coords = [
            (r, c)
            for r in range(self.rows)
            for c in range(self.cols)
            if (r, c) != exclude
        ]
        chosen = random.sample(all_coords, self.num_mines)
        for r, c in chosen:
            self._grid[r][c].is_mine = True

        # Compute adjacent mine counts
        for cell in self.cells():
            cell.adjacent_mines = sum(1 for n in cell.neighbors if n.is_mine)

        self._mines_placed = True

    def _flood_reveal(self, start: Cell) -> None:
        """BFS flood-fill revealing empty cells."""
        queue: List[Cell] = [start]
        visited: Set[Cell] = {start}

        while queue:
            cell = queue.pop(0)
            cell.state = CellState.REVEALED
            if cell.adjacent_mines == 0:
                for neighbor in cell.neighbors:
                    if neighbor not in visited and neighbor.state is CellState.HIDDEN:
                        visited.add(neighbor)
                        queue.append(neighbor)

    def _check_win(self) -> None:
        """Win when every non-mine cell is revealed."""
        for cell in self.cells():
            if not cell.is_mine and cell.state is not CellState.REVEALED:
                return
        self.game_state = GameState.WON
