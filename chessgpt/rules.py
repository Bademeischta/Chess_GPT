"""Custom move generation and rule enforcement logic."""

from dataclasses import dataclass
from typing import List, Optional, Set

FILES = 'abcdefgh'
RANKS = '12345678'

# movement offsets
KNIGHT_OFFSETS = [
    (-2, -1), (-2, 1), (-1, -2), (-1, 2),
    (1, -2), (1, 2), (2, -1), (2, 1)
]
BISHOP_OFFSETS = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
ROOK_OFFSETS = [(-1, 0), (1, 0), (0, -1), (0, 1)]
KING_OFFSETS = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),          (0, 1),
    (1, -1),  (1, 0), (1, 1)
]


def square_index(s: str) -> int:
    """Convert algebraic square (e.g. 'e4') to 0-63 index."""
    file = FILES.index(s[0])
    rank = 8 - int(s[1])
    return rank * 8 + file


def index_to_square(idx: int) -> str:
    return FILES[idx % 8] + RANKS[7 - idx // 8]


@dataclass(frozen=True)
class Move:
    from_sq: int
    to_sq: int
    promotion: Optional[str] = None

    @staticmethod
    def from_uci(uci: str) -> 'Move':
        promo = uci[4] if len(uci) > 4 else None
        return Move(square_index(uci[:2]), square_index(uci[2:4]), promo)

    def to_uci(self) -> str:
        base = index_to_square(self.from_sq) + index_to_square(self.to_sq)
        return base + (self.promotion or '')


@dataclass
class State:
    board: List[Optional[str]]  # 64 entries
    to_move: str               # 'w' or 'b'
    castling_rights: Set[str]
    en_passant: Optional[int]
    halfmove_clock: int
    fullmove_number: int
    history: List['State']

    @staticmethod
    def from_fen(fen: str) -> 'State':
        parts = fen.split()
        board_part, active, castling, ep, halfmove, fullmove = parts
        board: List[Optional[str]] = []
        for row in board_part.split('/'):
            for ch in row:
                if ch.isdigit():
                    board.extend([None] * int(ch))
                else:
                    board.append(ch)
        rights = set(castling) if castling != '-' else set()
        ep_sq = None if ep == '-' else square_index(ep)
        return State(
            board=board,
            to_move='w' if active == 'w' else 'b',
            castling_rights=rights,
            en_passant=ep_sq,
            halfmove_clock=int(halfmove),
            fullmove_number=int(fullmove),
            history=[],
        )

    def clone(self) -> 'State':
        return State(
            board=self.board[:],
            to_move=self.to_move,
            castling_rights=set(self.castling_rights),
            en_passant=self.en_passant,
            halfmove_clock=self.halfmove_clock,
            fullmove_number=self.fullmove_number,
            history=[h.clone() for h in self.history],
        )


def color_of(piece: str) -> str:
    return 'w' if piece.isupper() else 'b'


def opposite(color: str) -> str:
    return 'b' if color == 'w' else 'w'


def piece_at(state: State, row: int, col: int) -> Optional[str]:
    return state.board[row * 8 + col]


def set_piece(state: State, row: int, col: int, piece: Optional[str]) -> None:
    state.board[row * 8 + col] = piece


def is_square_attacked(state: State, row: int, col: int, attacker: str) -> bool:
    board = state.board
    # Pawn attacks
    directions = [(-1, -1), (-1, 1)] if attacker == 'w' else [(1, -1), (1, 1)]
    pawn = 'P' if attacker == 'w' else 'p'
    for dr, dc in directions:
        r, c = row + dr, col + dc
        if 0 <= r < 8 and 0 <= c < 8:
            if board[r * 8 + c] == pawn:
                return True
    # Knight
    for dr, dc in KNIGHT_OFFSETS:
        r, c = row + dr, col + dc
        if 0 <= r < 8 and 0 <= c < 8:
            piece = board[r * 8 + c]
            if piece and piece.lower() == 'n' and color_of(piece) == attacker:
                return True
    # Bishop/Queen
    for dr, dc in BISHOP_OFFSETS:
        r, c = row + dr, col + dc
        while 0 <= r < 8 and 0 <= c < 8:
            piece = board[r * 8 + c]
            if piece:
                if color_of(piece) == attacker and piece.lower() in ('b', 'q'):
                    return True
                break
            r += dr
            c += dc
    # Rook/Queen
    for dr, dc in ROOK_OFFSETS:
        r, c = row + dr, col + dc
        while 0 <= r < 8 and 0 <= c < 8:
            piece = board[r * 8 + c]
            if piece:
                if color_of(piece) == attacker and piece.lower() in ('r', 'q'):
                    return True
                break
            r += dr
            c += dc
    # King
    for dr, dc in KING_OFFSETS:
        r, c = row + dr, col + dc
        if 0 <= r < 8 and 0 <= c < 8:
            piece = board[r * 8 + c]
            if piece and piece.lower() == 'k' and color_of(piece) == attacker:
                return True
    return False


def king_position(state: State, color: str) -> Optional[tuple[int, int]]:
    target = 'K' if color == 'w' else 'k'
    for idx, piece in enumerate(state.board):
        if piece == target:
            return idx // 8, idx % 8
    return None


def in_check(state: State, color: str) -> bool:
    pos = king_position(state, color)
    if not pos:
        return False
    return is_square_attacked(state, pos[0], pos[1], opposite(color))


def add_move(moves: List[Move], from_sq: int, to_sq: int, promotion: Optional[str] = None) -> None:
    moves.append(Move(from_sq, to_sq, promotion))


def generate_pseudo_legal_moves(state: State) -> List[Move]:
    moves: List[Move] = []
    color = state.to_move
    for idx, piece in enumerate(state.board):
        if not piece or color_of(piece) != color:
            continue
        row, col = divmod(idx, 8)
        if piece.lower() == 'p':
            dir = -1 if color == 'w' else 1
            start = 6 if color == 'w' else 1
            promo_row = 0 if color == 'w' else 7
            # one forward
            r = row + dir
            if 0 <= r < 8 and piece_at(state, r, col) is None:
                if r == promo_row:
                    for p in 'qrbn':
                        add_move(moves, idx, r * 8 + col, p)
                else:
                    add_move(moves, idx, r * 8 + col)
                # double
                if row == start and piece_at(state, r + dir, col) is None:
                    add_move(moves, idx, (r + dir) * 8 + col)
            # captures
            for dc in (-1, 1):
                c = col + dc
                r = row + dir
                if 0 <= r < 8 and 0 <= c < 8:
                    target = piece_at(state, r, c)
                    if target and color_of(target) != color:
                        if r == promo_row:
                            for p in 'qrbn':
                                add_move(moves, idx, r * 8 + c, p)
                        else:
                            add_move(moves, idx, r * 8 + c)
                    elif state.en_passant == r * 8 + c:
                        add_move(moves, idx, r * 8 + c)
        elif piece.lower() == 'n':
            for dr, dc in KNIGHT_OFFSETS:
                r, c = row + dr, col + dc
                if 0 <= r < 8 and 0 <= c < 8:
                    target = piece_at(state, r, c)
                    if not target or color_of(target) != color:
                        add_move(moves, idx, r * 8 + c)
        elif piece.lower() == 'b':
            for dr, dc in BISHOP_OFFSETS:
                r, c = row + dr, col + dc
                while 0 <= r < 8 and 0 <= c < 8:
                    target = piece_at(state, r, c)
                    if target:
                        if color_of(target) != color:
                            add_move(moves, idx, r * 8 + c)
                        break
                    add_move(moves, idx, r * 8 + c)
                    r += dr
                    c += dc
        elif piece.lower() == 'r':
            for dr, dc in ROOK_OFFSETS:
                r, c = row + dr, col + dc
                while 0 <= r < 8 and 0 <= c < 8:
                    target = piece_at(state, r, c)
                    if target:
                        if color_of(target) != color:
                            add_move(moves, idx, r * 8 + c)
                        break
                    add_move(moves, idx, r * 8 + c)
                    r += dr
                    c += dc
        elif piece.lower() == 'q':
            for dr, dc in BISHOP_OFFSETS + ROOK_OFFSETS:
                r, c = row + dr, col + dc
                while 0 <= r < 8 and 0 <= c < 8:
                    target = piece_at(state, r, c)
                    if target:
                        if color_of(target) != color:
                            add_move(moves, idx, r * 8 + c)
                        break
                    add_move(moves, idx, r * 8 + c)
                    r += dr
                    c += dc
        elif piece.lower() == 'k':
            for dr, dc in KING_OFFSETS:
                r, c = row + dr, col + dc
                if 0 <= r < 8 and 0 <= c < 8:
                    target = piece_at(state, r, c)
                    if not target or color_of(target) != color:
                        add_move(moves, idx, r * 8 + c)
            # castling
            if color == 'w' and row == 7 and col == 4:
                if 'K' in state.castling_rights:
                    if piece_at(state, 7, 5) is None and piece_at(state, 7, 6) is None:
                        if not in_check(state, 'w') and not is_square_attacked(state, 7, 5, 'b') and not is_square_attacked(state, 7, 6, 'b') and piece_at(state, 7, 7) == 'R':
                            add_move(moves, idx, 7 * 8 + 6)
                if 'Q' in state.castling_rights:
                    if piece_at(state, 7, 3) is None and piece_at(state, 7, 2) is None and piece_at(state, 7, 1) is None:
                        if not in_check(state, 'w') and not is_square_attacked(state, 7, 3, 'b') and not is_square_attacked(state, 7, 2, 'b') and piece_at(state, 7, 0) == 'R':
                            add_move(moves, idx, 7 * 8 + 2)
            if color == 'b' and row == 0 and col == 4:
                if 'k' in state.castling_rights:
                    if piece_at(state, 0, 5) is None and piece_at(state, 0, 6) is None:
                        if not in_check(state, 'b') and not is_square_attacked(state, 0, 5, 'w') and not is_square_attacked(state, 0, 6, 'w') and piece_at(state, 0, 7) == 'r':
                            add_move(moves, idx, 0 * 8 + 6)
                if 'q' in state.castling_rights:
                    if piece_at(state, 0, 3) is None and piece_at(state, 0, 2) is None and piece_at(state, 0, 1) is None:
                        if not in_check(state, 'b') and not is_square_attacked(state, 0, 3, 'w') and not is_square_attacked(state, 0, 2, 'w') and piece_at(state, 0, 0) == 'r':
                            add_move(moves, idx, 0 * 8 + 2)
    return moves


def generate_legal_moves(state: State) -> List[Move]:
    moves = []
    for mv in generate_pseudo_legal_moves(state):
        tmp = state.clone()
        apply_move(tmp, mv)
        # nach apply_move ist tmp.to_move der Gegner,
        # also opposite(tmp.to_move) ist der Spieler, der gezogen hat
        if not in_check(tmp, opposite(tmp.to_move)):
            moves.append(mv)
    return moves


def apply_move(state: State, move: Move) -> None:
    board = state.board
    piece = board[move.from_sq]
    rights = set(state.castling_rights)
    row_from, col_from = divmod(move.from_sq, 8)
    row_to, col_to = divmod(move.to_sq, 8)
    capture = board[move.to_sq] is not None
    # en passant capture
    if piece.lower() == 'p' and move.to_sq == state.en_passant and board[move.to_sq] is None:
        if state.to_move == 'w':
            board[(row_to + 1) * 8 + col_to] = None
        else:
            board[(row_to - 1) * 8 + col_to] = None
        capture = True
    # move piece
    board[move.from_sq] = None
    board[move.to_sq] = piece
    # promotion
    if piece.lower() == 'p':
        end_row = 0 if state.to_move == 'w' else 7
        if row_to == end_row:
            board[move.to_sq] = move.promotion.upper() if state.to_move == 'w' else move.promotion.lower() if move.promotion else piece
    # castling move: move rook
    if piece.lower() == 'k':
        if abs(col_to - col_from) == 2:
            if col_to == 6:  # kingside
                rook_from = row_from * 8 + 7
                rook_to = row_from * 8 + 5
            else:  # queenside
                rook_from = row_from * 8 + 0
                rook_to = row_from * 8 + 3
            board[rook_to] = board[rook_from]
            board[rook_from] = None
        # update castling rights
        if state.to_move == 'w':
            rights.discard('K')
            rights.discard('Q')
        else:
            rights.discard('k')
            rights.discard('q')
    # rook movement affects rights
    if piece.lower() == 'r':
        if move.from_sq == 7 * 8 + 0:
            rights.discard('Q')
        elif move.from_sq == 7 * 8 + 7:
            rights.discard('K')
        elif move.from_sq == 0 * 8 + 0:
            rights.discard('q')
        elif move.from_sq == 0 * 8 + 7:
            rights.discard('k')
    # capture rook affects rights
    if capture:
        if move.to_sq == 7 * 8 + 0:
            rights.discard('Q')
        elif move.to_sq == 7 * 8 + 7:
            rights.discard('K')
        elif move.to_sq == 0 * 8 + 0:
            rights.discard('q')
        elif move.to_sq == 0 * 8 + 7:
            rights.discard('k')
    mover = state.to_move
    # en passant square
    if piece.lower() == 'p' and abs(row_to - row_from) == 2:
        ep_row = (row_from + row_to) // 2
        state.en_passant = ep_row * 8 + col_to
    else:
        state.en_passant = None

    # halfmove clock
    if piece.lower() == 'p' or capture:
        state.halfmove_clock = 0
    else:
        state.halfmove_clock += 1

    # fullmove number
    if mover == 'b':
        state.fullmove_number += 1

    # switch side
    state.to_move = opposite(state.to_move)

    state.castling_rights = ''.join(c for c in "KQkq" if c in rights)


def is_checkmate(state: State) -> bool:
    if in_check(state, state.to_move) and not generate_legal_moves(state):
        return True
    return False


def is_stalemate(state: State) -> bool:
    if not in_check(state, state.to_move) and not generate_legal_moves(state):
        return True
    return False


def is_draw_by_fifty_moves(state: State) -> bool:
    return state.halfmove_clock >= 100


def is_insufficient_material(state: State) -> bool:
    pieces = [p for p in state.board if p]
    pieces = [p.lower() for p in pieces if p.lower() != 'k']
    if not pieces:
        return True
    if pieces in (['n'], ['b']):
        return True
    return False
