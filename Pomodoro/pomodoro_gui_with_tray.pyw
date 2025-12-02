import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageDraw
import pystray
import sys
import time

class PomodoroApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pomodoro Timer")

        # 配置位置：画面右下
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = 300
        window_height = 250  # <<< 修正: 高さを250に変更
        x = screen_width - window_width - 20
        y = screen_height - window_height - 100
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")

        # スタイル設定：集中モード
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.9)
        self.root.configure(bg="black")

        # タイマー状態
        self.work_duration = tk.IntVar(value=25)
        self.break_duration = tk.IntVar(value=5)
        self.remaining = 0
        self.running = False
        self.is_work_session = True
        self.cycle_count = 0
        self.icon = None
        self.after_id = None

        self.create_widgets()
        self.bind_keys()

        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)

    def create_widgets(self):
        
        # <<< 修正: 上部の不要なラベルを削除

        self.canvas_size = 150
        self.arc_width = 6
        self.canvas = tk.Canvas(
            self.root, 
            width=self.canvas_size, 
            height=self.canvas_size, 
            bg="black", 
            highlightthickness=0
        )
        self.canvas.pack(pady=20)

        # 描画範囲の計算 (線の太さを考慮)
        coord = self.arc_width / 2
        size = self.canvas_size - self.arc_width

        # 1. 背景の円 (灰色)
        self.canvas.create_oval(
            coord, coord, size, size, 
            outline="gray", width=self.arc_width - 2
        )

        # 2. 残り時間を示す円弧 (赤色) (初期状態は0度)
        self.arc = self.canvas.create_arc(
            coord, coord, size, size,
            start=90,  # 12時の位置から開始
            extent=0,  # 最初は0度
            outline="#FF4500",  # トマトっぽい赤色
            width=self.arc_width,
            style=tk.ARC
        )

        # 3. 中央のデジタル時計テキスト
        self.timer_text = self.canvas.create_text(
            self.canvas_size / 2, self.canvas_size / 2,
            text="00:00",
            font=("Helvetica", 40),
            fill="white"
        )

        self.status_label = tk.Label(self.root, text="待機中", font=("Helvetica", 14), bg="black", fg="white")
        self.status_label.pack()

        self.cycle_label = tk.Label(self.root, text=f"今日の完了サイクル: {self.cycle_count}", font=("Helvetica", 12), bg="black", fg="white")
        self.cycle_label.pack(pady=5)

    def _cancel_timer(self):
        """既存の after ジョブをキャンセルする"""
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None

    def bind_keys(self):
        self.root.bind("<space>", self.toggle_timer_event)
        self.root.bind("<Escape>", self.reset_timer_event)
        self.root.bind("<Right>", self.skip_session_event)

    def toggle_timer_event(self, event): self.toggle_timer()
    def reset_timer_event(self, event): self.reset_timer()
    def skip_session_event(self, event): self.skip_session()

    def toggle_timer(self):
        if not self.running:
            # === 復帰ロジック ===
            
            # 残り時間がない場合 (リセット後など) は、新しいタイマーを開始
            if self.remaining <= 0:
                self.start_timer()
            else:
                # 一時停止から復帰する場合
                self.running = True
                # ステータスラベルを元に戻す
                status_text = "作業中" if self.is_work_session else "休憩中"
                self.status_label.config(text=status_text)
                # _run_session() を呼ばずに、updateループのみ再開
                self._update_timer()
        else:
            # === 一時停止ロジック ===
            self.running = False
            self._cancel_timer()
            self.status_label.config(text="一時停止中")
            if self.icon:
                self.icon.title = "一時停止中"
                
    def start_timer(self):
        self.running = True
        self._run_session()

    def reset_timer(self, event=None): # <<< 修正: event=None を追加
        self.running = False
        self._cancel_timer() # <<< 修正: タイマーをキャンセル
        self.remaining = 0
        
        self.canvas.itemconfig(self.timer_text, text="00:00")
        self.canvas.itemconfig(self.arc, extent=0)
        self.status_label.config(text="待機中")
        if self.icon:
            self.icon.title = "待機中"

    def skip_session(self, event=None): # <<< 修正: event=None を追加
        self.running = False
        self._cancel_timer() # <<< 修正: タイマーをキャンセル

        # <<< 修正: セッションを即座に切り替えるロジック
        if self.is_work_session:
            # 作業セッションをスキップした場合、サイクルカウントを増やす
            self.cycle_count += 1
            self.update_cycle_label()
        
        # セッションを反転
        self.is_work_session = not self.is_work_session
        # 次のセッションを開始
        self.start_timer()

    def _run_session(self):
        duration = self.work_duration.get() * 60 if self.is_work_session else self.break_duration.get() * 60
        self.remaining = duration
        self.canvas.itemconfig(self.arc, extent=360)
        self._update_timer()

    def _update_timer(self):

        start_process_time = time.time()

        if not self.running:
            return

        if self.remaining >= 0: # 0秒の表示も行うため >= に変更
            
            # 1. 角度の計算
            total_duration = self.work_duration.get() * 60 if self.is_work_session else self.break_duration.get() * 60
            if total_duration == 0: total_duration = 1 # ゼロ除算防止
            
            angle = (self.remaining / total_duration) * 360
            self.canvas.itemconfig(self.arc, extent=angle)

            # 2. デジタル時計テキストの更新
            mins, secs = divmod(self.remaining, 60)
            time_str = f"{mins:02d}:{secs:02d}"
            self.canvas.itemconfig(self.timer_text, text=time_str)

            # 3. トレイアイコンのテキスト更新
            if self.remaining > 0:
                status_text = "作業中" if self.is_work_session else "休憩中"
                self.status_label.config(text=status_text)
                if self.icon:
                    self.icon.title = f"{status_text}: {time_str}"
            
            # 4. 次の更新へ
            if self.remaining > 0:
                self.remaining -= 1
                # 処理終了時刻を記録
                end_process_time = time.time()
                
                # 今回の処理にかかった時間 (ミリ秒)
                process_duration_ms = (end_process_time - start_process_time) * 1000
                
                # 次にafterで待つべき時間 (1000ms - 処理時間)
                delay = int(1000 - process_duration_ms)

                # もし処理時間が1秒を超えていたら、最小遅延(1ms)ですぐ次を実行
                if delay < 1:
                    delay = 1
                
                # <<< 修正: 二重呼び出しを削除し、IDを正しく保存する
                self.after_id = self.root.after(delay, self._update_timer)
                
            else:
                # 5. 残り時間が0になった時の処理
                self.running = False
                self.after_id = None # ループ終了
                
                if self.is_work_session:
                    self.cycle_count += 1
                    self.update_cycle_label()
                    messagebox.showinfo("完了", "作業セッション完了！休憩しましょう。")
                else:
                    messagebox.showinfo("休憩終了", "休憩が終わりました！次の作業へ。")

                self.is_work_session = not self.is_work_session
                self.start_timer()

    def update_cycle_label(self):
        self.cycle_label.config(text=f"今日の完了サイクル: {self.cycle_count}")

    def hide_window(self):
        self.root.withdraw()

    def show_window(self, icon=None, item=None):
        self.root.after(0, lambda: (
            self.root.deiconify(),
            self.root.attributes("-topmost", True)
        ))

    def quit_app(self, icon=None, item=None):
        self.running = False
        self._cancel_timer() # 念のため終了時にもタイマーを止める
        if self.icon:
            self.icon.stop()
        self.root.quit()
        sys.exit()

    def show_help(self, icon=None, item=None):
        """操作方法のメッセージボックスを表示する"""
        help_text = """
【キーボード操作】
  ・スペース: 開始 / 一時停止
  ・Esc: タイマーリセット
  ・→ (右矢印): 現在のセッションをスキップ
"""
        # メインスレッドでメッセージボックスを実行
        self.root.after(0, lambda: messagebox.showinfo("操作方法", help_text, parent=self.root))

    def create_icon_image(self):
        image = Image.new("RGB", (64, 64), "black")
        draw = ImageDraw.Draw(image)
        draw.ellipse((8, 8, 56, 56), fill=(255, 60, 60))  # トマト本体
        draw.polygon([(32, 4), (24, 12), (32, 10), (40, 12)], fill=(0, 255, 0))  # ヘタ
        return image

def run_tray(app_instance):
    icon = pystray.Icon("pomodoro")
    icon.icon = app_instance.create_icon_image()
    icon.menu = pystray.Menu(
        pystray.MenuItem("再表示", app_instance.show_window),
        pystray.MenuItem("操作方法", app_instance.show_help),
        pystray.MenuItem("終了", app_instance.quit_app)
    )
    app_instance.icon = icon
    icon.run_detached()

if __name__ == "__main__":
    root = tk.Tk()
    app = PomodoroApp(root)
    run_tray(app)
    root.mainloop()
