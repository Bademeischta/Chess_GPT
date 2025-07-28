import chess
from dataclasses import dataclass

@dataclass
class ChessBoard:
    """Wrapper around python-chess Board with undo functionality."""
    board: chess.Board
    history: list[str]

    def __init__(self, fen: str | None = None):
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

    def get_legal_moves(self) -> list[chess.Move]:
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

