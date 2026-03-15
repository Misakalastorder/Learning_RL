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
    - E：提前终止并按子数判胜负保存日志
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
        self.root.bind("<Key-e>", lambda e: self.end_game_by_count())
        self.root.bind("<Key-E>", lambda e: self.end_game_by_count())

        if self.logger is not None and self.mode != MODE_REPLAY:
            self.logger.start_new_game(board_size=self.game.size, mode=self.mode)

        self.draw_board()
        self.update_status()

        # 若是 AI 执黑，启动时先让 AI 落子
        self.root.after(200, self.maybe_ai_move)
        # 启动后也检查是否一开始就无合法着手（极端情况/重放切换后）
        self.root.after(250, self._auto_end_if_no_legal_moves)

    def _count_stones(self) -> tuple[int, int]:
        black = 0
        white = 0
        for y in range(self.game.size):
            for x in range(self.game.size):
                s = self.game.get(x, y)
                if s == 1:
                    black += 1
                elif s == 2:
                    white += 1
        return black, white

    def _determine_winner_by_count(self) -> tuple[str, str, int, int]:
        black, white = self._count_stones()
        if black > white:
            return "black", "black_win", black, white
        if white > black:
            return "white", "white_win", black, white
        return "draw", "draw", black, white

    def _finish_game_and_save(self, *, end_reason: str) -> None:
        if self.logger is None or self.mode == MODE_REPLAY:
            self.quit_program()
            return
        winner, result, black, white = self._determine_winner_by_count()
        self.logger.end_game(
            result=result,
            winner=winner,
            black_count=black,
            white_count=white,
            end_reason=end_reason,
        )
        path = self.logger.save()
        if path:
            messagebox.showinfo(
                "对局结束",
                f"结果：{result}\n黑子：{black}  白子：{white}\n日志已保存到：\n{path}",
            )
        self.quit_program()

    def _auto_end_if_no_legal_moves(self) -> None:
        """
        任何一方轮到自己走但没有合法着手时：自动结束对局并记录。
        注意：这里按需求直接结束（不做围棋“弃手”规则）。
        """
        if self.mode == MODE_REPLAY:
            return
        if self.logger is None:
            return
        legal = self.game.get_legal_moves(self.game.current_player)
        if not legal:
            self.update_status("当前方无合法着手：对局自动结束并保存")
            # 稍微延迟一下让状态栏可见
            self.root.after(50, lambda: self._finish_game_and_save(end_reason="no_legal_moves"))

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

        # 若轮到的人类一方已经无合法着手，直接结束对局
        self._auto_end_if_no_legal_moves()

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

        # 检查下一手是否已无合法着手（自动结束）
        self._auto_end_if_no_legal_moves()

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

        # AI 回合开始前：若已无合法着手则直接结束
        self._auto_end_if_no_legal_moves()

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
            # 根据需求：任何一方无合法着手就直接结束并记录
            self.update_status("AI 无合法着手：对局自动结束并保存")
            self.root.after(50, lambda: self._finish_game_and_save(end_reason="no_legal_moves"))
            return

        x, y = move
        if not self.game.play_move(x, y):
            # 极少数情况下（例如规则变更导致不合法）简单跳过
            return

        if self.logger is not None:
            self.logger.log_move((x, y), current_player)

        self.draw_board()
        self.update_status()

        # 检查下一手是否无合法着手（自动结束）
        self._auto_end_if_no_legal_moves()

        if self.mode == MODE_AI_VS_AI:
            # 连续自动下棋，给一个小延迟以便肉眼观察
            self.root.after(10, self.maybe_ai_move)
            # self.root.after(200, self.maybe_ai_move)

    # 日志与重放
    def end_game_and_save(self) -> None:
        if self.logger is None or self.mode == MODE_REPLAY:
            self.quit_program()
            return
        self._finish_game_and_save(end_reason="manual_end")

    def end_game_by_count(self) -> None:
        """
        提前终止对局并按场上子数判胜负保存日志（E 键）。
        """
        if self.mode == MODE_REPLAY:
            return
        self._finish_game_and_save(end_reason="manual_end_by_count")

    def replay_from_file(self) -> None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        initial_dir = os.path.join(base_dir, "record")
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

