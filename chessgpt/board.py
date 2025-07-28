"""State container delegating rule logic to rules module."""

from dataclasses import dataclass, field
from typing import List, Optional

from . import rules
import chess


@dataclass
class Board:
    state: rules.State
    history: List[rules.State] = field(default_factory=list)

    def __init__(self, fen: Optional[str] = None) -> None:
        self.state = rules.State.from_fen(
            fen or "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        )
        self.history = []

    def make_move(self, move: rules.Move) -> None:
        if move not in rules.generate_legal_moves(self.state):
            raise ValueError("Illegal move")
        self.history.append(self.state.clone())
        rules.apply_move(self.state, move)

    def undo_move(self) -> None:
        if not self.history:
            raise ValueError("No move to undo")
        self.state = self.history.pop()

    def get_legal_moves(self) -> List[rules.Move]:
        return rules.generate_legal_moves(self.state)

    def is_checkmate(self) -> bool:
        return rules.is_checkmate(self.state)

    def is_stalemate(self) -> bool:
        return rules.is_stalemate(self.state)

    def is_draw_by_fifty_moves(self) -> bool:
        return rules.is_draw_by_fifty_moves(self.state)

    def is_insufficient_material(self) -> bool:
        return rules.is_insufficient_material(self.state)


@dataclass
class ChessBoard:
    """Wrapper around python-chess Board with undo functionality."""

    board: chess.Board
    history: List[str]

    def __init__(self, fen: str | None = None) -> None:
        self.board = chess.Board(fen) if fen else chess.Board()
        self.history = []

    def make_move(self, move: chess.Move) -> None:
        if move not in self.board.legal_moves:
            raise ValueError("Illegal move")
        self.history.append(self.board.fen())
        self.board.push(move)

    def undo_move(self) -> None:
        if not self.history:
            raise ValueError("No move to undo")
        fen = self.history.pop()
        self.board.set_fen(fen)

    def get_legal_moves(self) -> List[chess.Move]:
        return list(self.board.legal_moves)

    # Terminal state checks
    def is_checkmate(self) -> bool:
        return self.board.is_checkmate()

    def is_stalemate(self) -> bool:
        return self.board.is_stalemate()

    def is_draw_by_fifty_moves(self) -> bool:
        return self.board.can_claim_fifty_moves()

    def is_insufficient_material(self) -> bool:
        return self.board.is_insufficient_material()

    def is_draw_by_repetition(self) -> bool:
        return self.board.is_repetition()
