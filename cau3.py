# cau3_gui.py - Nâng cấp giao diện với ttkbootstrap (dark theme)
import tkinter as tk
from tkinter import messagebox
import requests
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("TkAgg")
import numpy as np

try:
    import ttkbootstrap as ttk
    from ttkbootstrap.constants import *
    from ttkbootstrap.scrolled import ScrolledFrame
    USE_BOOTSTRAP = True
except ImportError:
    from tkinter import ttk
    USE_BOOTSTRAP = False
    print("[WARN] ttkbootstrap không tìm thấy, dùng ttk thuần. Cài: pip install ttkbootstrap")

API_URL = "http://127.0.0.1:5000/api/player/"

# ── Màu sắc chủ đạo ──────────────────────────────────────────────────────────
CLR_BG       = "#0d1117"   # nền chính - đen navy
CLR_SURFACE  = "#161b22"   # card / frame nền
CLR_BORDER   = "#30363d"   # viền
CLR_P1       = "#3b82f6"   # cầu thủ 1 - xanh dương
CLR_P2       = "#ef4444"   # cầu thủ 2 - đỏ
CLR_ACCENT   = "#22c55e"   # nút compare - xanh lá
CLR_TEXT     = "#e6edf3"   # chữ chính
CLR_MUTED    = "#8b949e"   # chữ phụ
CLR_HOVER    = "#1a7f37"   # hover nút compare
FONT_MAIN    = ("Segoe UI", 10)
FONT_BOLD    = ("Segoe UI", 10, "bold")
FONT_TITLE   = ("Segoe UI", 13, "bold")
FONT_SMALL   = ("Segoe UI", 9)

# ─────────────────────────────────────────────────────────────────────────────

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("⚽  So sánh Cầu thủ – EPL")
        self.root.geometry("680x620")
        self.root.resizable(True, True)
        self.root.configure(bg=CLR_BG)
        self._apply_dark_style()

        # ── Header ────────────────────────────────────────────────────────────
        header = tk.Frame(root, bg=CLR_BG)
        header.pack(fill="x", padx=20, pady=(16, 4))
        tk.Label(header, text="⚽  EPL Player Comparator",
                 font=FONT_TITLE, bg=CLR_BG, fg=CLR_TEXT).pack(side="left")
        tk.Label(header, text="powered by Flask API",
                 font=FONT_SMALL, bg=CLR_BG, fg=CLR_MUTED).pack(side="right", pady=4)

        # ── Search cards ──────────────────────────────────────────────────────
        search_outer = tk.Frame(root, bg=CLR_BG)
        search_outer.pack(fill="x", padx=20, pady=8)

        self.data1, self.data2 = None, None

        self.card1, self.entry1, self.status1 = self._make_player_card(
            search_outer, "Cầu thủ 1", CLR_P1, 1)
        self.card2, self.entry2, self.status2 = self._make_player_card(
            search_outer, "Cầu thủ 2", CLR_P2, 2)

        # ── Stats checkbox panel ───────────────────────────────────────────────
        stats_outer = tk.Frame(root, bg=CLR_BG)
        stats_outer.pack(fill="both", expand=True, padx=20, pady=(4, 0))

        lbl_frame_title = tk.Label(stats_outer,
            text="Chọn chỉ số để so sánh  (chọn ít nhất 3 ô)",
            font=FONT_BOLD, bg=CLR_BG, fg=CLR_MUTED)
        lbl_frame_title.pack(anchor="w", pady=(0, 6))

        # scrollable container
        self.scroll_container = tk.Frame(stats_outer, bg=CLR_SURFACE,
                                         bd=1, relief="flat",
                                         highlightbackground=CLR_BORDER,
                                         highlightthickness=1)
        self.scroll_container.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(self.scroll_container, bg=CLR_SURFACE,
                                highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(self.scroll_container, orient="vertical",
                                  command=self.canvas.yview)
        self.stats_frame = tk.Frame(self.canvas, bg=CLR_SURFACE)

        self.stats_frame.bind("<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")))
        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.stats_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.bind("<Configure>",
            lambda e: self.canvas.itemconfig(
                self.canvas_window, width=e.width))
        # mouse wheel scroll
        self.canvas.bind_all("<MouseWheel>",
            lambda e: self.canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        self.vars = {}

        # ── Compare button ────────────────────────────────────────────────────
        btn_frame = tk.Frame(root, bg=CLR_BG)
        btn_frame.pack(fill="x", padx=20, pady=12)

        self.compare_btn = tk.Button(
            btn_frame, text="📊  So sánh / Compare",
            font=("Segoe UI", 11, "bold"),
            bg=CLR_ACCENT, fg="white",
            activebackground=CLR_HOVER, activeforeground="white",
            relief="flat", bd=0, cursor="hand2",
            padx=24, pady=10,
            command=self.draw_radar,
            state="disabled")
        self.compare_btn.pack()
        self.compare_btn.bind("<Enter>",
            lambda e: self.compare_btn.config(bg=CLR_HOVER))
        self.compare_btn.bind("<Leave>",
            lambda e: self.compare_btn.config(bg=CLR_ACCENT))

        # ── Status bar ────────────────────────────────────────────────────────
        self.statusbar = tk.Label(root,
            text="  Nhập tên cầu thủ và nhấn Tìm kiếm để bắt đầu.",
            font=FONT_SMALL, bg=CLR_SURFACE, fg=CLR_MUTED,
            anchor="w", pady=5)
        self.statusbar.pack(fill="x", side="bottom")

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _apply_dark_style(self):
        style = ttk.Style()
        if USE_BOOTSTRAP:
            # ttkbootstrap: chọn theme tối
            try:
                self.root.style = ttk.Style(theme="darkly")
            except Exception:
                pass
        style.configure("TScrollbar",
                        background=CLR_SURFACE, troughcolor=CLR_BG,
                        arrowcolor=CLR_MUTED, bordercolor=CLR_BG)

    def _make_player_card(self, parent, label, accent_color, player_num):
        """Tạo card tìm kiếm cho một cầu thủ."""
        card = tk.Frame(parent, bg=CLR_SURFACE,
                        highlightbackground=accent_color,
                        highlightthickness=2)
        card.pack(side="left", fill="both", expand=True,
                  padx=(0 if player_num == 2 else 0, 8 if player_num == 1 else 0),
                  pady=2, ipadx=10, ipady=10)
        if player_num == 2:
            card.pack_configure(padx=(8, 0))

        # accent bar top
        bar = tk.Frame(card, bg=accent_color, height=3)
        bar.pack(fill="x")

        inner = tk.Frame(card, bg=CLR_SURFACE)
        inner.pack(fill="x", padx=10, pady=8)

        icon = "🔵" if player_num == 1 else "🔴"
        tk.Label(inner, text=f"{icon}  {label}",
                 font=FONT_BOLD, bg=CLR_SURFACE,
                 fg=accent_color).pack(anchor="w")

        entry = tk.Entry(inner, font=FONT_MAIN, width=18,
                         bg=CLR_BG, fg=CLR_TEXT,
                         insertbackground=CLR_TEXT,
                         relief="flat",
                         highlightbackground=CLR_BORDER,
                         highlightthickness=1)
        entry.pack(fill="x", pady=(4, 6))

        # ── Placeholder ───────────────────────────────────────────────────────
        _PH = "VD: Salah, Haaland..."
        entry.insert(0, _PH)
        entry.config(fg=CLR_MUTED)

        def _on_focus_in(e, en=entry, ph=_PH):
            if en.get() == ph:
                en.delete(0, "end")
                en.config(fg=CLR_TEXT)

        def _on_focus_out(e, en=entry, ph=_PH):
            if en.get().strip() == "":
                en.delete(0, "end")
                en.insert(0, ph)
                en.config(fg=CLR_MUTED)

        entry.bind("<FocusIn>",  _on_focus_in)
        entry.bind("<FocusOut>", _on_focus_out)
        # search on Enter key
        entry.bind("<Return>", lambda e: self.search_player(player_num))

        btn = tk.Button(inner,
            text="🔍  Tìm kiếm",
            font=FONT_SMALL, bg=accent_color, fg="white",
            activebackground=self._darken(accent_color),
            activeforeground="white",
            relief="flat", bd=0, cursor="hand2",
            padx=10, pady=5,
            command=lambda: self.search_player(player_num))
        btn.pack(anchor="w")
        btn.bind("<Enter>", lambda e, b=btn, c=accent_color:
                 b.config(bg=self._darken(c)))
        btn.bind("<Leave>", lambda e, b=btn, c=accent_color:
                 b.config(bg=c))

        status = tk.Label(inner, text="⏳ Chưa tải",
                          font=FONT_SMALL, bg=CLR_SURFACE,
                          fg=CLR_MUTED, wraplength=180, justify="left")
        status.pack(anchor="w", pady=(6, 0))

        return card, entry, status

    @staticmethod
    def _darken(hex_color):
        """Tối màu ~20% để dùng cho hover."""
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        r, g, b = max(0, int(r*0.75)), max(0, int(g*0.75)), max(0, int(b*0.75))
        return f"#{r:02x}{g:02x}{b:02x}"

    # ── Core logic (giữ nguyên) ────────────────────────────────────────────────

    def search_player(self, player_num):
        name = self.entry1.get() if player_num == 1 else self.entry2.get()
        _PH = "VD: Salah, Haaland..."
        if not name or name == _PH:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập tên cầu thủ!")
            return

        status_lbl = self.status1 if player_num == 1 else self.status2
        status_lbl.config(text="⏳ Đang tải...", fg="#f59e0b")
        self.root.update_idletasks()

        try:
            res = requests.get(API_URL + name, timeout=5)
            if res.status_code == 200:
                data = res.json()
                info_text = (
                    f"✅ {data['Player']}\n"
                    f"🏟 {data.get('Squad','?')} • {data.get('Pos','?')} • {data.get('Age','?')} tuổi"
                )
                if player_num == 1:
                    self.data1 = data
                    status_lbl.config(
                        text=info_text, fg="#22c55e",
                        wraplength=180, justify="left")
                    self.generate_checkboxes()
                else:
                    self.data2 = data
                    status_lbl.config(
                        text=info_text, fg="#22c55e",
                        wraplength=180, justify="left")
                self.statusbar.config(
                    text=f"  ✅ Tìm thấy: {data['Player']}", fg="#22c55e")
                if self.data1 and self.data2:
                    self.compare_btn.config(state="normal")
            else:
                status_lbl.config(text=f"❌ Không tìm thấy", fg=CLR_P2)
                self.statusbar.config(
                    text=f"  ❌ Không tìm thấy cầu thủ: {name}", fg=CLR_P2)
                messagebox.showerror("Lỗi", f"Không tìm thấy cầu thủ: {name}")
        except Exception as e:
            status_lbl.config(text="❌ Lỗi kết nối", fg=CLR_P2)
            self.statusbar.config(
                text="  ❌ Không thể kết nối API. Hãy chắc chắn đã chạy cau2_api.py", fg=CLR_P2)
            messagebox.showerror("Lỗi API",
                "Không thể kết nối! Hãy chắc chắn bạn đã chạy cau2_api.py")

    def generate_checkboxes(self):
        for widget in self.stats_frame.winfo_children():
            widget.destroy()
        self.vars.clear()

        numeric_stats = []
        for k, v in self.data1.items():
            if k not in ['Player', 'Nation', 'Pos', 'Squad', 'Age', 'Born', 'STT']:
                try:
                    float(v)
                    numeric_stats.append(k)
                except ValueError:
                    pass

        display_stats = numeric_stats[:18]   # mở rộng lên 18 mục (có scroll)

        COLS = 3

        # ── Nút chọn / bỏ chọn tất cả ──────────────────────────────────────
        ctrl_frame = tk.Frame(self.stats_frame, bg=CLR_SURFACE)
        ctrl_frame.grid(row=0, column=0, columnspan=COLS,
                        sticky="w", padx=6, pady=(6, 2))
        tk.Button(ctrl_frame,
                  text="Chọn tất cả",
                  font=FONT_SMALL, fg=CLR_MUTED,
                  bg=CLR_SURFACE, activebackground=CLR_BG,
                  activeforeground=CLR_TEXT,
                  relief="flat", bd=0, cursor="hand2",
                  command=lambda: [v.set(True) for v in self.vars.values()]
                  ).pack(side="left", padx=(0, 8))
        tk.Button(ctrl_frame,
                  text="Bỏ chọn tất cả",
                  font=FONT_SMALL, fg=CLR_MUTED,
                  bg=CLR_SURFACE, activebackground=CLR_BG,
                  activeforeground=CLR_TEXT,
                  relief="flat", bd=0, cursor="hand2",
                  command=lambda: [v.set(False) for v in self.vars.values()]
                  ).pack(side="left")

        # ── Checkboxes (bắt đầu từ row 1) ───────────────────────────────────
        for i, stat in enumerate(display_stats):
            var = tk.BooleanVar(value=True if i < 5 else False)
            self.vars[stat] = var

            cb = tk.Checkbutton(
                self.stats_frame,
                text=stat,
                variable=var,
                font=FONT_SMALL,
                bg=CLR_SURFACE, fg=CLR_TEXT,
                selectcolor=CLR_BG,
                activebackground=CLR_SURFACE,
                activeforeground=CLR_TEXT,
                relief="flat",
                cursor="hand2",
                padx=8, pady=4)
            cb.grid(row=i // COLS + 1, column=i % COLS,
                    sticky="w", padx=6, pady=2)

        # update scrollregion
        self.stats_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def draw_radar(self):
        if not self.data1 or not self.data2:
            messagebox.showwarning("Cảnh báo", "Vui lòng tìm kiếm đủ 2 cầu thủ!")
            return

        selected_stats = [stat for stat, var in self.vars.items() if var.get()]
        if len(selected_stats) < 3:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn ít nhất 3 chỉ số!")
            return

        def get_val(data, stat):
            try:
                return float(data.get(stat, 0))
            except:
                return 0.0

        vals1 = [get_val(self.data1, stat) for stat in selected_stats]
        vals2 = [get_val(self.data2, stat) for stat in selected_stats]

        # Normalize từng cặp giá trị theo stat
        for i in range(len(selected_stats)):
            max_v = max(vals1[i], vals2[i])
            if max_v > 0:
                vals1[i] /= max_v
                vals2[i] /= max_v

        angles = np.linspace(0, 2 * np.pi, len(selected_stats),
                             endpoint=False).tolist()
        vals1 += vals1[:1]
        vals2 += vals2[:1]
        angles += angles[:1]

        # ── Matplotlib dark styling ───────────────────────────────────────────
        plt.style.use("dark_background")
        fig, ax = plt.subplots(figsize=(7, 6), subplot_kw=dict(polar=True))
        fig.patch.set_facecolor("#0d1117")
        ax.set_facecolor("#161b22")

        ax.fill(angles, vals1, color=CLR_P1, alpha=0.25)
        ax.plot(angles, vals1, color=CLR_P1, linewidth=2,
                label=self.data1['Player'])

        ax.fill(angles, vals2, color=CLR_P2, alpha=0.25)
        ax.plot(angles, vals2, color=CLR_P2, linewidth=2,
                label=self.data2['Player'])

        ax.set_yticks([0.25, 0.5, 0.75, 1.0])
        ax.set_yticklabels(['25%', '50%', '75%', '100%'], fontsize=7, color=CLR_MUTED)
        ax.set_xticks(angles[:-1])
        short_labels = [s.split('_')[-1] for s in selected_stats]
        ax.set_xticklabels(short_labels, fontsize=9, color=CLR_TEXT)
        ax.tick_params(colors=CLR_MUTED)
        ax.spines['polar'].set_color(CLR_BORDER)
        ax.grid(color=CLR_BORDER, linestyle="--", alpha=0.6)

        plt.legend(loc='upper right', bbox_to_anchor=(1.35, 1.15),
                   facecolor=CLR_SURFACE, edgecolor=CLR_BORDER,
                   labelcolor=CLR_TEXT, fontsize=9)
        plt.title(
            f"⚽  {self.data1['Player']}  vs  {self.data2['Player']}\n(values normalized per stat)",
            y=1.1, fontweight='bold', fontsize=11, color=CLR_TEXT)
        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    if USE_BOOTSTRAP:
        root = ttk.Window(themename="darkly")
    else:
        root = tk.Tk()
    app = App(root)
    root.mainloop()