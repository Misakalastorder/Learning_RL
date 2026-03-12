from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple


Stone = int  # 0 = empty, 1 = black, 2 = white
Point = Tuple[int, int]


@dataclass
class GoGame:
    """
    非严格完整规则的简化围棋逻辑：
    - 只禁止在已有棋子的位置落子
    - 允许简单吃子：如果对方一块棋的气被占完，则整块提走
    - 暂不实现打劫、复杂禁入点判定等高级规则
    如需严格规则，可在此模块基础上逐步扩展。
    """

    size: int = 19
    board: List[List[Stone]] = field(init=False)
    current_player: Stone = 1  # 1 = black, 2 = white
    move_history: List[Tuple[Optional[Point], Stone]] = field(
        default_factory=list
    )  # (坐标或 None 表示弃手, 落子方)

    def __post_init__(self) -> None:
        self.board = [[0 for _ in range(self.size)] for _ in range(self.size)]

    # 基础工具方法
    def is_on_board(self, x: int, y: int) -> bool:
        return 0 <= x < self.size and 0 <= y < self.size

    def get(self, x: int, y: int) -> Stone:
        return self.board[y][x]

    def set(self, x: int, y: int, stone: Stone) -> None:
        self.board[y][x] = stone

    def neighbors(self, x: int, y: int) -> List[Point]:
        res: List[Point] = []
        if x > 0:
            res.append((x - 1, y))
        if x < self.size - 1:
            res.append((x + 1, y))
        if y > 0:
            res.append((x, y - 1))
        if y < self.size - 1:
            res.append((x, y + 1))
        return res

    # 提子与气
    def _collect_group(
        self, x: int, y: int, visited: Optional[set[Point]] = None
    ) -> Tuple[set[Point], set[Point]]:
        """返回：该块棋的所有棋子位置集合、该块所有气的位置集合。"""
        if visited is None:
            visited = set()
        color = self.get(x, y)
        if color == 0:
            return set(), set()
        group: set[Point] = set()
        liberties: set[Point] = set()
        stack: List[Point] = [(x, y)]
        visited.add((x, y))
        while stack:
            cx, cy = stack.pop()
            group.add((cx, cy))
            for nx, ny in self.neighbors(cx, cy):
                stone = self.get(nx, ny)
                if stone == 0:
                    liberties.add((nx, ny))
                elif stone == color and (nx, ny) not in visited:
                    visited.add((nx, ny))
                    stack.append((nx, ny))
        return group, liberties

    def _remove_group(self, group: set[Point]) -> None:
        for x, y in group:
            self.set(x, y, 0)

    # 合法性与落子
    def is_legal_move(self, x: int, y: int, player: Optional[Stone] = None) -> bool:
        """只检查是否在棋盘、是否为空位。高级规则（自杀、打劫）暂不限制。"""
        if player is None:
            player = self.current_player
        if not self.is_on_board(x, y):
            return False
        if self.get(x, y) != 0:
            return False
        # 如需自杀禁入等，可在此处增加检查逻辑。
        return True

    def play_move(self, x: Optional[int], y: Optional[int]) -> bool:
        """
        执行一步棋。
        - (None, None) 表示当前玩家弃手。
        - 返回是否落子成功。
        """
        if x is None or y is None:
            # 弃手
            self.move_history.append((None, self.current_player))
            self._switch_player()
            return True

        if not self.is_legal_move(x, y, self.current_player):
            return False

        # 落子
        self.set(x, y, self.current_player)

        # 提走周围被吃的敌方棋块（无气）
        opponent: Stone = 1 if self.current_player == 2 else 2
        to_remove: set[Point] = set()
        visited: set[Point] = set()
        for nx, ny in self.neighbors(x, y):
            if self.is_on_board(nx, ny) and self.get(nx, ny) == opponent:
                if (nx, ny) in visited:
                    continue
                group, libs = self._collect_group(nx, ny, visited)
                if not libs:
                    to_remove.update(group)

        if to_remove:
            self._remove_group(to_remove)

        # 记录历史
        self.move_history.append(((x, y), self.current_player))
        self._switch_player()
        return True

    def _switch_player(self) -> None:
        self.current_player = 1 if self.current_player == 2 else 2

    def get_legal_moves(self, player: Optional[Stone] = None) -> List[Point]:
        if player is None:
            player = self.current_player
        moves: List[Point] = []
        for y in range(self.size):
            for x in range(self.size):
                if self.is_legal_move(x, y, player):
                    moves.append((x, y))
        return moves

    def reset(self) -> None:
        self.board = [[0 for _ in range(self.size)] for _ in range(self.size)]
        self.current_player = 1
        self.move_history.clear()

