from __future__ import annotations

import os
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Callable, Optional

from .ai import get_ai_move
from .logger import GameLogger
from .rules import GoGame, Point, Stone


# 对弈模式常量
MODE_HUMAN_BLACK_AI_WHITE = "human_black_ai_white"
MODE_AI_BLACK_HUMAN_WHITE = "ai_black_human_white"
MODE_HUMAN_VS_HUMAN = "human_vs_human"
MODE_AI_VS_AI = "ai_vs_ai"
MODE_REPLAY = "replay"


class GoGUI:
    """
    使用 tkinter 绘制棋盘，支持鼠标点击落子。
    - Esc：退出程序
    - N：开始新对局
    - R：选择日志文件并重放对局
    - Q：结束当前对局并保存日志（若有）
    """

    def __init__(
        self,
        root: tk.Tk,
        game: GoGame,
        mode: str,
        logger: Optional[GameLogger] = None,
    ) -> None:
        self.root = root
        self.game = game
        self.mode = mode
        self.logger = logger

        self.cell_size = 32
        self.margin = 40
        self.board_pixel_size = self.margin * 2 + self.cell_size * (self.game.size - 1)

        self.root.title("Python 围棋")
        self.canvas = tk.Canvas(
            root,
            width=self.board_pixel_size,
            height=self.board_pixel_size,
            bg="#DDB88C",
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # 状态栏
        self.status_var = tk.StringVar()
        self.status_label = tk.Label(root, textvariable=self.status_var)
        self.status_label.pack(fill=tk.X)

        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.root.bind("<Escape>", lambda e: self.quit_program())
        self.root.bind("<Key-n>", lambda e: self.new_game())
        self.root.bind("<Key-N>", lambda e: self.new_game())
        self.root.bind("<Key-r>", lambda e: self.replay_from_file())
        self.root.bind("<Key-R>", lambda e: self.replay_from_file())
        self.root.bind("<Key-q>", lambda e: self.end_game_and_save())
        self.root.bind("<Key-Q>", lambda e: self.end_game_and_save())

        if self.logger is not None and self.mode != MODE_REPLAY:
            self.logger.start_new_game(board_size=self.game.size, mode=self.mode)

        self.draw_board()
        self.update_status()

        # 若是 AI 执黑，启动时先让 AI 落子
        self.root.after(200, self.maybe_ai_move)

    # 坐标变换
    def board_to_pixel(self, x: int, y: int) -> tuple[int, int]:
        px = self.margin + x * self.cell_size
        py = self.margin + y * self.cell_size
        return px, py

    def pixel_to_board(self, px: int, py: int) -> Optional[Point]:
        x = round((px - self.margin) / self.cell_size)
        y = round((py - self.margin) / self.cell_size)
        if 0 <= x < self.game.size and 0 <= y < self.game.size:
            return x, y
        return None

    # 绘制相关
    def draw_board(self) -> None:
        self.canvas.delete("all")
        size = self.game.size
        # 画网格线
        for i in range(size):
            x0, y0 = self.board_to_pixel(0, i)
            x1, y1 = self.board_to_pixel(size - 1, i)
            self.canvas.create_line(x0, y0, x1, y1)

            x0, y0 = self.board_to_pixel(i, 0)
            x1, y1 = self.board_to_pixel(i, size - 1)
            self.canvas.create_line(x0, y0, x1, y1)

        # 画棋子
        radius = self.cell_size * 0.45
        for y in range(size):
            for x in range(size):
                stone = self.game.get(x, y)
                if stone == 0:
                    continue
                px, py = self.board_to_pixel(x, y)
                color = "black" if stone == 1 else "white"
                self.canvas.create_oval(
                    px - radius,
                    py - radius,
                    px + radius,
                    py + radius,
                    fill=color,
                    outline="black",
                )

    def update_status(self, extra: str = "") -> None:
        if self.mode == MODE_REPLAY:
            text = "当前模式：重放对局（R 选择其他日志，Esc 退出）"
        else:
            player = "黑棋" if self.game.current_player == 1 else "白棋"
            text = f"当前行棋方：{player}    模式：{self.mode}"
        if extra:
            text += " | " + extra
        self.status_var.set(text)

    # 事件处理
    def on_canvas_click(self, event: tk.Event) -> None:
        if self.mode == MODE_REPLAY:
            return  # 重放模式不允许点击落子

        point = self.pixel_to_board(event.x, event.y)
        if point is None:
            return

        x, y = point
        current_player = self.game.current_player

        # 根据模式判断当前是否由人类落子
        if not self._is_human_turn(current_player):
            return

        if not self.game.play_move(x, y):
            self.update_status("该位置不能落子")
            return

        if self.logger is not None:
            self.logger.log_move((x, y), current_player)

        self.draw_board()
        self.update_status()

        # 人类落子后轮到 AI 的情况
        self.root.after(200, self.maybe_ai_move)

    def _is_human_turn(self, player: Stone) -> bool:
        if self.mode == MODE_HUMAN_BLACK_AI_WHITE:
            return player == 1
        if self.mode == MODE_AI_BLACK_HUMAN_WHITE:
            return player == 2
        if self.mode == MODE_HUMAN_VS_HUMAN:
            return True
        if self.mode == MODE_AI_VS_AI:
            return False
        return False

    # AI 行动 / AI vs AI
    def maybe_ai_move(self) -> None:
        if self.mode == MODE_REPLAY:
            return

        current_player = self.game.current_player
        is_ai_turn = False
        if self.mode == MODE_HUMAN_BLACK_AI_WHITE and current_player == 2:
            is_ai_turn = True
        elif self.mode == MODE_AI_BLACK_HUMAN_WHITE and current_player == 1:
            is_ai_turn = True
        elif self.mode == MODE_AI_VS_AI:
            is_ai_turn = True

        if not is_ai_turn:
            return

        move = get_ai_move(self.game, current_player)
        if move is None:
            self.update_status("AI 无合法着手，可能对局已接近结束")
            return

        x, y = move
        if not self.game.play_move(x, y):
            # 极少数情况下（例如规则变更导致不合法）简单跳过
            return

        if self.logger is not None:
            self.logger.log_move((x, y), current_player)

        self.draw_board()
        self.update_status()

        if self.mode == MODE_AI_VS_AI:
            # 连续自动下棋，给一个小延迟以便肉眼观察
            self.root.after(200, self.maybe_ai_move)

    # 日志与重放
    def end_game_and_save(self) -> None:
        if self.logger is None or self.mode == MODE_REPLAY:
            self.quit_program()
            return
        self.logger.end_game(result="manually_ended")
        path = self.logger.save()
        if path:
            messagebox.showinfo("保存完成", f"对局日志已保存到：\n{path}")
        self.quit_program()

    def replay_from_file(self) -> None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        initial_dir = os.path.join(base_dir, "records")
        if not os.path.isdir(initial_dir):
            initial_dir = base_dir
        path = filedialog.askopenfilename(
            title="选择对局日志文件",
            initialdir=initial_dir,
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
        )
        if not path:
            return

        from .logger import GameLogger

        data = GameLogger.load_log(path)
        self._replay_from_data(data)

    def _replay_from_data(self, data: dict) -> None:
        meta = data.get("meta", {})
        moves = data.get("moves", [])

        size = int(meta.get("board_size", self.game.size))
        if size != self.game.size:
            self.game = GoGame(size=size)
        else:
            self.game.reset()

        self.mode = MODE_REPLAY
        self.draw_board()
        self.update_status("开始重放")

        def step(i: int) -> None:
            if i >= len(moves):
                self.update_status("重放结束（Esc 退出，R 重放其他对局）")
                return
            mr = moves[i]
            x = mr.get("x")
            y = mr.get("y")
            player = mr.get("player", 1)
            if x is None or y is None:
                self.game.play_move(None, None)
            else:
                # 直接写入并切换当前行棋方，重现历史
                self.game.current_player = player
                self.game.play_move(x, y)
            self.draw_board()
            self.update_status(f"重放第 {i + 1} 手")
            self.root.after(300, lambda: step(i + 1))

        step(0)

    # 其他控制
    def new_game(self) -> None:
        if self.mode == MODE_REPLAY:
            # 重放模式下按 N 等价于重置为“人类黑 vs AI 白”默认模式
            self.mode = MODE_HUMAN_BLACK_AI_WHITE
        self.game.reset()
        if self.logger is not None:
            self.logger.start_new_game(board_size=self.game.size, mode=self.mode)
        self.draw_board()
        self.update_status("新对局开始")
        self.root.after(200, self.maybe_ai_move)

    def quit_program(self) -> None:
        self.root.quit()

