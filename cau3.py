# cau3_gui.py
import tkinter as tk
from tkinter import messagebox
import requests
import matplotlib.pyplot as plt
import numpy as np

API_URL = "http://127.0.0.1:5000/api/player/"

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("So sanh cau thu - EPL")
        self.root.geometry("600x500")

        search_frame = tk.Frame(root)
        search_frame.pack(pady=10)

        tk.Label(search_frame, text="Cau thu 1:").grid(row=0, column=0, padx=5, pady=5)
        self.entry1 = tk.Entry(search_frame)
        self.entry1.grid(row=0, column=1, padx=5, pady=5)
        tk.Button(search_frame, text="Tim kiem 1", command=lambda: self.search_player(1)).grid(row=0, column=2, padx=5, pady=5)
        self.status1 = tk.Label(search_frame, text="Chua tai", fg="red")
        self.status1.grid(row=0, column=3, padx=5)

        tk.Label(search_frame, text="Cau thu 2:").grid(row=1, column=0, padx=5, pady=5)
        self.entry2 = tk.Entry(search_frame)
        self.entry2.grid(row=1, column=1, padx=5, pady=5)
        tk.Button(search_frame, text="Tim kiem 2", command=lambda: self.search_player(2)).grid(row=1, column=2, padx=5, pady=5)
        self.status2 = tk.Label(search_frame, text="Chua tai", fg="red")
        self.status2.grid(row=1, column=3, padx=5)

        self.data1, self.data2 = None, None
        
        self.stats_frame = tk.LabelFrame(root, text="Chon chi so de so sanh (Tich it nhat 3 o)")
        self.stats_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.vars = {} 

        tk.Button(root, text="So sanh / Compare", command=self.draw_radar, bg="lightblue", font=("Arial", 10, "bold")).pack(pady=10)

    def search_player(self, player_num):
        name = self.entry1.get() if player_num == 1 else self.entry2.get()
        if not name:
            messagebox.showwarning("Canh bao", "Vui long nhap ten cau thu!")
            return
            
        try:
            res = requests.get(API_URL + name)
            if res.status_code == 200:
                data = res.json()
                if player_num == 1:
                    self.data1 = data
                    self.status1.config(text=f"Da tim thay: {data['Player']}", fg="green")
                    self.generate_checkboxes() 
                else:
                    self.data2 = data
                    self.status2.config(text=f"Da tim thay: {data['Player']}", fg="green")
            else:
                messagebox.showerror("Loi", f"Khong tim thay cau thu: {name}")
        except Exception as e:
            messagebox.showerror("Loi API", "Khong the ket noi! Hay chac chan ban da chay cau2_api.py")

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
        
        display_stats = numeric_stats[:12]

        for i, stat in enumerate(display_stats):
            var = tk.BooleanVar(value=True if i < 5 else False)
            self.vars[stat] = var
            tk.Checkbutton(self.stats_frame, text=stat, variable=var).grid(row=i//2, column=i%2, sticky="w", padx=10)

    def draw_radar(self):
        if not self.data1 or not self.data2:
            messagebox.showwarning("Canh bao", "Vui long tim kiem du 2 cau thu!")
            return

        selected_stats = [stat for stat, var in self.vars.items() if var.get()]
        if len(selected_stats) < 3:
            messagebox.showwarning("Canh bao", "Vui long chon it nhat 3 chi so!")
            return

        def get_val(data, stat):
            try: return float(data.get(stat, 0))
            except: return 0.0

        vals1 = [get_val(self.data1, stat) for stat in selected_stats]
        vals2 = [get_val(self.data2, stat) for stat in selected_stats]

        angles = np.linspace(0, 2 * np.pi, len(selected_stats), endpoint=False).tolist()
        vals1 += vals1[:1]
        vals2 += vals2[:1]
        angles += angles[:1]

        fig, ax = plt.subplots(figsize=(7, 6), subplot_kw=dict(polar=True))
        ax.fill(angles, vals1, color='blue', alpha=0.25)
        ax.plot(angles, vals1, color='blue', linewidth=2, label=self.data1['Player'])
        
        ax.fill(angles, vals2, color='red', alpha=0.25)
        ax.plot(angles, vals2, color='red', linewidth=2, label=self.data2['Player'])

        ax.set_yticks([])
        ax.set_xticks(angles[:-1])
        short_labels = [s.split('_')[-1] for s in selected_stats]
        ax.set_xticklabels(short_labels, fontsize=9)
        
        plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
        plt.title(f"So sanh: {self.data1['Player']} va {self.data2['Player']}", y=1.08, fontweight='bold')
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()