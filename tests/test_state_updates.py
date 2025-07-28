import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from chessgpt import Board, rules


def test_en_passant_and_halfmove_after_double_push():
    board = Board()
    board.make_move(rules.Move.from_uci("e2e4"))
    assert board.state.en_passant == rules.square_index("e3")
    assert board.state.halfmove_clock == 0


def test_en_passant_cleared_after_single_push():
    board = Board()
    board.make_move(rules.Move.from_uci("e2e4"))
    board.make_move(rules.Move.from_uci("e7e6"))
    assert board.state.en_passant is None


def test_halfmove_clock_increments_on_quiet_move():
    board = Board()
    board.make_move(rules.Move.from_uci("e2e4"))
    board.make_move(rules.Move.from_uci("e7e5"))
    board.make_move(rules.Move.from_uci("g1f3"))
    assert board.state.halfmove_clock == 1


def test_fullmove_increment_after_black_move():
    board = Board()
    board.make_move(rules.Move.from_uci("e2e4"))
    board.make_move(rules.Move.from_uci("e7e5"))
    assert board.state.fullmove_number == 2


def test_king_move_removes_castling_rights():
    fen = "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"
    board = Board(fen)
    board.make_move(rules.Move.from_uci("e1e2"))
    assert "K" not in board.state.castling_rights
    assert "Q" not in board.state.castling_rights


def test_rook_move_removes_castling_rights():
    fen = "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"
    board = Board(fen)
    board.make_move(rules.Move.from_uci("a1a2"))
    assert "Q" not in board.state.castling_rights


def test_rook_move_removes_kingside_rights():
    fen = "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"
    board = Board(fen)
    board.make_move(rules.Move.from_uci("h1h2"))
    assert "K" not in board.state.castling_rights


def test_capture_rook_removes_castling_rights():
    fen = "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"
    board = Board(fen)
    board.make_move(rules.Move.from_uci("a1a8"))  # capture rook on a8
    assert "q" not in board.state.castling_rights


def test_capture_rook_removes_black_kingside_rights():
    fen = "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"
    board = Board(fen)
    board.make_move(rules.Move.from_uci("h1h8"))  # capture rook on h8
    assert "k" not in board.state.castling_rights


def test_to_move_switches_after_move():
    board = Board()
    current = board.state.to_move
    board.make_move(rules.Move.from_uci("e2e4"))
    assert board.state.to_move != current
