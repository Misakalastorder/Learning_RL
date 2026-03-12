from __future__ import annotations

import random
from typing import Optional, Tuple

from .rules import GoGame, Point, Stone


def random_ai_move(game: GoGame, player: Optional[Stone] = None) -> Optional[Point]:
    """
    随机策略：
    - 从当前合法落子点中随机选择一个
    - 若无合法点则返回 None（视为无子可下，可由上层逻辑处理为弃手或终局）
    """
    if player is None:
        player = game.current_player
    legal_moves = game.get_legal_moves(player)
    if not legal_moves:
        return None
    return random.choice(legal_moves)


def get_ai_move(game: GoGame, player: Optional[Stone] = None) -> Optional[Point]:
    """
    对外统一调用入口。
    后续如果要切换为更复杂的策略，可在此处替换实现。
    """
    return random_ai_move(game, player)

