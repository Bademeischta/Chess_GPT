import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


from chessgpt import Board, rules


def test_castling_moves():
    fen = 'r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1'
    board = Board(fen)
    mv = rules.Move.from_uci('e1g1')
    assert mv in board.get_legal_moves()
    board.make_move(mv)
    assert 'K' not in board.state.castling_rights
    mv2 = rules.Move.from_uci('e8c8')
    board.make_move(mv2)
    assert 'k' not in board.state.castling_rights


def test_illegal_castling_due_to_attack():
    fen = 'r3k2r/8/8/6r1/8/8/8/R3K2R w KQkq - 0 1'
    board = Board(fen)
    mv = rules.Move.from_uci('e1g1')
    assert mv not in board.get_legal_moves()


def test_castling_rights_lost_after_king_move():
    fen = '4k3/8/8/8/8/8/8/R3K2R w KQ - 0 1'
    board = Board(fen)
    board.make_move(rules.Move.from_uci('e1f1'))
    board.make_move(rules.Move.from_uci('e8e7'))
    board.make_move(rules.Move.from_uci('f1e1'))
    assert 'K' not in board.state.castling_rights
    assert rules.Move.from_uci('e1g1') not in board.get_legal_moves()


def test_pawn_promotion_default():
    fen = '8/P7/8/8/8/8/7p/7K w - - 0 1'
    board = Board(fen)
    board.make_move(rules.Move.from_uci('a7a8q'))
    assert board.state.board[rules.square_index('a8')] == 'Q'


def test_pawn_promotion_black_knight():
    fen = '7k/8/8/8/8/8/p6P/7K b - - 0 1'
    board = Board(fen)
    board.make_move(rules.Move.from_uci('a2a1n'))
    assert board.state.board[rules.square_index('a1')] == 'n'


def test_illegal_promotion():
    fen = '8/8/P7/8/8/8/7p/7K w - - 0 1'
    board = Board(fen)
    mv = rules.Move.from_uci('a6a7q')
    assert mv not in board.get_legal_moves()


def test_en_passant_capture():
    board = Board()
    board.make_move(rules.Move.from_uci('e2e4'))
    board.make_move(rules.Move.from_uci('a7a6'))
    board.make_move(rules.Move.from_uci('e4e5'))
    board.make_move(rules.Move.from_uci('d7d5'))
    mv = rules.Move.from_uci('e5d6')
    assert mv in board.get_legal_moves()
    board.make_move(mv)
    assert board.state.board[rules.square_index('d5')] is None


def test_en_passant_not_available_later():
    board = Board()
    board.make_move(rules.Move.from_uci('e2e4'))
    board.make_move(rules.Move.from_uci('a7a6'))
    board.make_move(rules.Move.from_uci('e4e5'))
    board.make_move(rules.Move.from_uci('d7d5'))
    board.make_move(rules.Move.from_uci('h2h3'))
    mv = rules.Move.from_uci('e5d6')
    assert mv not in board.get_legal_moves()


def test_en_passant_requires_double_push():
    board = Board()
    board.make_move(rules.Move.from_uci('e2e4'))
    board.make_move(rules.Move.from_uci('d7d6'))
    board.make_move(rules.Move.from_uci('e4e5'))
    board.make_move(rules.Move.from_uci('d6d5'))
    mv = rules.Move.from_uci('e5d6')
    assert mv not in board.get_legal_moves()


def test_fifty_move_rule_draw():
    fen = '8/8/8/8/8/8/8/K1k5 w - - 100 1'
    board = Board(fen)
    assert board.is_draw_by_fifty_moves()


def test_halfmove_clock_resets_on_pawn_move():
    fen = '8/8/p7/8/8/8/P7/K1k5 w - - 99 1'
    board = Board(fen)
    board.make_move(rules.Move.from_uci('a2a3'))
    assert board.state.halfmove_clock == 0
    assert not board.is_draw_by_fifty_moves()


def test_halfmove_clock_resets_on_capture():
    board = Board()
    board.state.halfmove_clock = 99
    board.state.board[rules.square_index('a2')] = 'P'
    board.state.board[rules.square_index('b3')] = 'p'
    board.make_move(rules.Move.from_uci('a2b3'))
    assert board.state.halfmove_clock == 0
    assert not board.is_draw_by_fifty_moves()


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

