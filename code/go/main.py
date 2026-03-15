from __future__ import annotations

import tkinter as tk

from mylib.gui import (
    GoGUI,
    MODE_AI_BLACK_HUMAN_WHITE,
    MODE_AI_VS_AI,
    MODE_HUMAN_BLACK_AI_WHITE,
    MODE_HUMAN_VS_HUMAN,
)
from mylib.logger import GameLogger
from mylib.rules import GoGame

# 通过修改下面这个变量来选择对弈模式：
# - "human_black_ai_white" : 用户执黑，电脑执白
# - "ai_black_human_white" : 电脑执黑，用户执白
# - "human_vs_human"       : 两个用户轮流下棋
# - "ai_vs_ai"             : 两个电脑轮流下棋
# GAME_MODE = MODE_HUMAN_BLACK_AI_WHITE
GAME_MODE = MODE_AI_VS_AI
# 默认棋盘大小（已选：19 路）
BOARD_SIZE = 19


def main() -> None:
    game = GoGame(size=BOARD_SIZE)
    logger = GameLogger(log_dir="record")

    root = tk.Tk()
    GoGUI(root, game, mode=GAME_MODE, logger=logger)
    root.mainloop()


if __name__ == "__main__":
    main()

