import tkinter as tk
from tkinter import messagebox
import time
import threading
from datetime import datetime

class PomodoroApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pomodoro Timer")

        # 初期設定
        self.work_duration = tk.IntVar(value=25)  # 分
        self.break_duration = tk.IntVar(value=5)  # 分
        self.remaining = 0
        self.running = False
        self.is_work_session = True
        self.cycle_count = 0

        self.create_widgets()

    def create_widgets(self):
        tk.Label(self.root, text="作業時間（分）").pack()
        tk.Entry(self.root, textvariable=self.work_duration).pack()

        tk.Label(self.root, text="休憩時間（分）").pack()
        tk.Entry(self.root, textvariable=self.break_duration).pack()

        self.timer_label = tk.Label(self.root, text="00:00", font=("Helvetica", 32))
        self.timer_label.pack(pady=10)

        self.status_label = tk.Label(self.root, text="待機中", font=("Helvetica", 14))
        self.status_label.pack()

        self.start_button = tk.Button(self.root, text="スタート", command=self.start_timer)
        self.start_button.pack(side=tk.LEFT, padx=20, pady=10)

        self.reset_button = tk.Button(self.root, text="リセット", command=self.reset_timer)
        self.reset_button.pack(side=tk.RIGHT, padx=20, pady=10)

    def start_timer(self):
        if not self.running:
            self.running = True
            self.is_work_session = True
            self._run_session()

    def reset_timer(self):
        self.running = False
        self.remaining = 0
        self.timer_label.config(text="00:00")
        self.status_label.config(text="待機中")

    def _run_session(self):
        duration = self.work_duration.get() * 60 if self.is_work_session else self.break_duration.get() * 60
        self.remaining = duration
        self._update_timer()

    def _update_timer(self):
        if self.running and self.remaining > 0:
            mins, secs = divmod(self.remaining, 60)
            self.timer_label.config(text=f"{mins:02d}:{secs:02d}")
            self.status_label.config(text="作業中" if self.is_work_session else "休憩中")
            self.remaining -= 1
            self.root.after(1000, self._update_timer)
        elif self.running:
            if self.is_work_session:
                self.cycle_count += 1  # 1サイクル終了
                messagebox.showinfo("完了", "作業セッション完了！休憩しましょう。")
            else:
                messagebox.showinfo("休憩終了", "休憩が終わりました！次の作業へ。")
            self.is_work_session = not self.is_work_session
            self._run_session()

if __name__ == "__main__":
    root = tk.Tk()
    app = PomodoroApp(root)
    root.mainloop()
