import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import chess
from chessgpt.board import ChessBoard


def test_castling_move():
    fen = 'r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1'
    board = ChessBoard(fen)
    board.make_move(chess.Move.from_uci('e1g1'))
    assert not board.board.has_kingside_castling_rights(chess.WHITE)
    assert board.board.has_queenside_castling_rights(chess.BLACK)
    board.make_move(chess.Move.from_uci('e8c8'))
    assert board.board.castling_rights == 0


def test_en_passant_and_undo():
    board = ChessBoard()
    board.make_move(chess.Move.from_uci('e2e4'))
    board.make_move(chess.Move.from_uci('a7a6'))
    board.make_move(chess.Move.from_uci('e4e5'))
    board.make_move(chess.Move.from_uci('d7d5'))
    # en passant available on d6
    moves = board.get_legal_moves()
    assert chess.Move.from_uci('e5d6') in moves
    board.make_move(chess.Move.from_uci('e5d6'))
    assert board.board.piece_at(chess.D5) is None
    board.undo_move()
    assert board.board.turn == chess.WHITE
    assert board.board.piece_at(chess.D5).symbol().lower() == 'p'


def test_undo_series_returns_to_start():
    board = ChessBoard()
    moves = ['e2e4', 'e7e5', 'g1f3', 'b8c6']
    for uci in moves:
        board.make_move(chess.Move.from_uci(uci))
    for _ in moves[::-1]:
        board.undo_move()
    assert board.board.board_fen() == chess.Board().board_fen()
    assert board.board.turn == chess.WHITE
