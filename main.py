"""
Sudoku Game — PySide6 (Dark macOS Edition)
Author: Artur S.

- 9x9 grid with QLineEdit cells
- Difficulty selector (Easy/Medium/Hard)
- Auto-generate puzzle with unique solution
- Auto-solver (backtracking)
- Input validation (red for errors)
- Modern dark theme UI (macOS look)
"""

import sys
import random
from typing import List, Optional, Tuple
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGridLayout, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QMessageBox
)
from PySide6.QtGui import QIntValidator, QFont
from PySide6.QtCore import Qt

Board = List[List[int]]

# ---------------- Sudoku Logic ---------------- #


def find_empty(board: Board) -> Optional[Tuple[int, int]]:
    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:
                return r, c
    return None


def is_safe(board: Board, row: int, col: int, num: int) -> bool:
    if num in board[row]:
        return False
    if any(board[x][col] == num for x in range(9)):
        return False
    box_row, box_col = 3 * (row // 3), 3 * (col // 3)
    for r in range(box_row, box_row + 3):
        for c in range(box_col, box_col + 3):
            if board[r][c] == num:
                return False
    return True


def solve_backtracking(board: Board) -> bool:
    spot = find_empty(board)
    if not spot:
        return True
    r, c = spot
    for num in range(1, 10):
        if is_safe(board, r, c, num):
            board[r][c] = num
            if solve_backtracking(board):
                return True
            board[r][c] = 0
    return False


def count_solutions(board: Board, limit: int = 2) -> int:
    spot = find_empty(board)
    if not spot:
        return 1
    r, c = spot
    count = 0
    for num in range(1, 10):
        if is_safe(board, r, c, num):
            board[r][c] = num
            count += count_solutions(board, limit)
            board[r][c] = 0
            if count >= limit:
                break
    return count


def generate_full_board() -> Board:
    board = [[0] * 9 for _ in range(9)]
    nums = list(range(1, 10))

    def fill_cell(idx: int) -> bool:
        if idx == 81:
            return True
        r, c = divmod(idx, 9)
        random.shuffle(nums)
        for n in nums:
            if is_safe(board, r, c, n):
                board[r][c] = n
                if fill_cell(idx + 1):
                    return True
                board[r][c] = 0
        return False

    fill_cell(0)
    return board


def make_puzzle(full: Board, holes: int) -> Board:
    puzzle = [row[:] for row in full]
    cells = [(r, c) for r in range(9) for c in range(9)]
    random.shuffle(cells)
    removed = 0
    for r, c in cells:
        if removed >= holes:
            break
        backup = puzzle[r][c]
        puzzle[r][c] = 0
        temp = [row[:] for row in puzzle]
        if count_solutions(temp, 2) == 1:
            removed += 1
        else:
            puzzle[r][c] = backup
    return puzzle


DIFFICULTY = {"Հեշտ": 36, "Միջին": 45, "Դժվար": 54}

# ---------------- GUI ---------------- #

DARK_STYLE = """
QMainWindow {
    background-color: #2b2b2b;
}

QLineEdit {
    background-color: #3c3c3c;
    color: #ffffff;
    border: 1px solid #555555;
    border-radius: 4px;
    font-size: 16px;
    font-weight: bold;
}

QLineEdit:read-only {
    background-color: #666666;
    color: #ffffff;
}

QPushButton {
    background-color: #4a4a4a;
    color: #ffffff;
    border: 1px solid #888888;
    border-radius: 6px;
    padding: 5px 10px;
}

QPushButton:hover {
    background-color: #5a5a5a;
}

QLabel {
    color: #ffffff;
    font-weight: bold;
    font-size: 14px;
}

QComboBox {
    background-color: #3c3c3c;
    color: #ffffff;
    border: 1px solid #777777;
    border-radius: 6px;
    padding: 2px 6px;
}
"""


class Cell(QLineEdit):
    def __init__(self, row: int, col: int):
        super().__init__()
        self.row = row
        self.col = col
        self.fixed = False
        self.setMaxLength(1)
        self.setAlignment(Qt.AlignCenter)
        self.setFont(QFont("Arial", 16))
        self.setValidator(QIntValidator(1, 9))

    def set_fixed(self, value: bool):
        self.fixed = value
        if value:
            self.setReadOnly(True)
            self.setStyleSheet(
                "background-color: #555555; color: white; font-weight: bold;")
        else:
            self.setReadOnly(False)
            self.setStyleSheet("background-color: #3c3c3c; color: white;")


class SudokuApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sudoku — macOS Edition")
        self.grid_cells = []
        self.solution = None

        container = QWidget()
        vbox = QVBoxLayout(container)
        self.setCentralWidget(container)

        # Controls
        hbox = QHBoxLayout()
        vbox.addLayout(hbox)
        hbox.addWidget(QLabel("Դժվարություն:"))
        self.combo = QComboBox()
        self.combo.addItems(DIFFICULTY.keys())
        hbox.addWidget(self.combo)

        self.btn_generate = QPushButton("Գեներացնել")
        self.btn_solve = QPushButton("Լուծել")
        self.btn_check = QPushButton("Ստուգել")
        self.btn_clear = QPushButton("Մաքրել")
        for b in [self.btn_generate, self.btn_solve, self.btn_check,
                  self.btn_clear]:
            hbox.addWidget(b)

        # Grid
        grid = QGridLayout()
        vbox.addLayout(grid)
        for r in range(9):
            row = []
            for c in range(9):
                cell = Cell(r, c)
                # alternating 3x3 background shades
                if ((r // 3) + (c // 3)) % 2 == 0:
                    cell.setStyleSheet(
                        "background-color:#3a3a3a; color:white; \
                        border-radius:3px;")
                else:
                    cell.setStyleSheet(
                        "background-color:#2e2e2e; color:white;\
                        border-radius:3px;")
                grid.addWidget(cell, r, c)
                row.append(cell)
            self.grid_cells.append(row)

        # Events
        self.btn_generate.clicked.connect(self.generate)
        self.btn_solve.clicked.connect(self.solve)
        self.btn_check.clicked.connect(self.check)
        self.btn_clear.clicked.connect(self.clear)

    def read_board(self):
        board = [[0]*9 for _ in range(9)]
        for r in range(9):
            for c in range(9):
                text = self.grid_cells[r][c].text()
                board[r][c] = int(text) if text.isdigit() else 0
        return board

    def write_board(self, board: Board, fixed_mask=None):
        for r in range(9):
            for c in range(9):
                val = board[r][c]
                cell = self.grid_cells[r][c]
                cell.setText(str(val) if val else "")
                cell.set_fixed(fixed_mask[r][c] if fixed_mask else False)

    def generate(self):
        difficulty = self.combo.currentText()
        holes = DIFFICULTY[difficulty]
        full = generate_full_board()
        puzzle = make_puzzle(full, holes)
        self.solution = full
        mask = [[puzzle[r][c] != 0 for c in range(9)] for r in range(9)]
        self.write_board(puzzle, mask)

    def solve(self):
        board = self.read_board()
        if solve_backtracking(board):
            self.write_board(board)
        else:
            QMessageBox.warning(self, "Error", "Չի գտնվել լուծում")

    def check(self):
        board = self.read_board()
        for r in range(9):
            for c in range(9):
                val = board[r][c]
                cell = self.grid_cells[r][c]
                if val == 0:
                    continue
                board[r][c] = 0
                ok = is_safe(board, r, c, val)
                board[r][c] = val
                color = "red" if not ok else "white"
                cell.setStyleSheet(
                    f"color:{color}; background-color:#3c3c3c; \
                        border-radius:3px;")
        QMessageBox.information(self, "Ստուգում", "Ստուգումն ավարտված է")

    def clear(self):
        for r in range(9):
            for c in range(9):
                cell = self.grid_cells[r][c]
                if not cell.fixed:
                    cell.clear()


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_STYLE)
    win = SudokuApp()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
