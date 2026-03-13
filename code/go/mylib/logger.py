from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .rules import Point, Stone


@dataclass
class MoveRecord:
    x: Optional[int]
    y: Optional[int]
    player: Stone


@dataclass
class GameMeta:
    board_size: int
    mode: str
    started_at: str
    finished_at: Optional[str] = None
    result: Optional[str] = None  # 自由文本，如 “black_win”“white_win”“draw”
    winner: Optional[str] = None  # "black" | "white" | "draw" | None
    black_count: Optional[int] = None
    white_count: Optional[int] = None
    end_reason: Optional[str] = None  # 如 "no_legal_moves" / "manual_end" 等


class GameLogger:
    """
    简单日志模块：
    - 每局对局保存为一个 JSON 文件
    - 文件内容包括：元信息 meta、所有落子 moves
    - 可通过 load_log 读取并用于重放
    """

    def __init__(self, log_dir: str = "record") -> None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.log_dir = os.path.join(base_dir, log_dir)
        os.makedirs(self.log_dir, exist_ok=True)

        self.meta: Optional[GameMeta] = None
        self.moves: List[MoveRecord] = []

    def start_new_game(self, board_size: int, mode: str) -> None:
        self.meta = GameMeta(
            board_size=board_size,
            mode=mode,
            started_at=datetime.now().isoformat(timespec="seconds"),
        )
        self.moves = []

    def log_move(self, point: Optional[Point], player: Stone) -> None:
        if self.meta is None:
            # 未调用 start_new_game 的防御
            self.start_new_game(board_size=19, mode="unknown")
        if point is None:
            x, y = None, None
        else:
            x, y = point
        self.moves.append(MoveRecord(x=x, y=y, player=player))

    def end_game(
        self,
        result: Optional[str] = None,
        *,
        winner: Optional[str] = None,
        black_count: Optional[int] = None,
        white_count: Optional[int] = None,
        end_reason: Optional[str] = None,
    ) -> None:
        if self.meta is None:
            return
        self.meta.finished_at = datetime.now().isoformat(timespec="seconds")
        if result is not None:
            self.meta.result = result
        if winner is not None:
            self.meta.winner = winner
        if black_count is not None:
            self.meta.black_count = black_count
        if white_count is not None:
            self.meta.white_count = white_count
        if end_reason is not None:
            self.meta.end_reason = end_reason

    def save(self) -> str:
        if self.meta is None:
            # 若从未 start 过，对局为空也不保存
            return ""
        data: Dict[str, Any] = {
            "meta": asdict(self.meta),
            "moves": [asdict(m) for m in self.moves],
        }
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"game_{ts}.json"
        path = os.path.join(self.log_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return path

    @staticmethod
    def load_log(path: str) -> Dict[str, Any]:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

