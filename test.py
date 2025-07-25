import tkinter as tk
from tkinter import messagebox
from PIL import ImageTk, Image

class KillTrackerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ARMA StatTrak™ GUI")
        self.root.geometry("400x350")
        self.root.configure(bg="#1e1e1e")

        # Fonts & Colors
        label_font = ("Consolas", 14)
        streak_font = ("Consolas", 12, "italic")
        fg_color = "#00ff00"

        # Header
        tk.Label(root, text="🔫 ARMA StatTrak™", font=("Consolas", 16, "bold"),
                 bg="#1e1e1e", fg="#ffffff").pack(pady=10)

        # Stats Grid
        self.kills_var = tk.StringVar(value="Kills: 0 / 0")
        self.veh_kills_var = tk.StringVar(value="Vehicle Kills: 0 / 0")
        self.streak_var = tk.StringVar(value="")

        tk.Label(root, textvariable=self.kills_var, font=label_font, fg=fg_color, bg="#1e1e1e").pack()
        tk.Label(root, textvariable=self.veh_kills_var, font=label_font, fg=fg_color, bg="#1e1e1e").pack()
        tk.Label(root, textvariable=self.streak_var, font=streak_font, fg="#ffaa00", bg="#1e1e1e").pack(pady=5)

        # Buttons
        btn_frame = tk.Frame(root, bg="#1e1e1e")
        btn_frame.pack(pady=15)

        tk.Button(btn_frame, text="🖼️ Debug Screenshot", command=self.take_screenshot,
                  width=20, bg="#333", fg="white").grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="♻️ Reset Session", command=self.reset_session,
                  width=20, bg="#333", fg="white").grid(row=1, column=0, padx=5, pady=5)
        tk.Button(btn_frame, text="❌ Exit", command=self.root.quit,
                  width=20, bg="#ff4444", fg="white").grid(row=2, column=0, padx=5)

    def update_stats(self, kills, total_kills, vkills, total_vkills, streak_msg):
        self.kills_var.set(f"Kills: {kills} / {total_kills}")
        self.veh_kills_var.set(f"Vehicle Kills: {vkills} / {total_vkills}")
        self.streak_var.set(streak_msg)

    def take_screenshot(self):
        # Placeholder: Hook into real region capture
        messagebox.showinfo("Screenshot", "Debug screenshot taken!")

    def reset_session(self):
        # Placeholder: Reset logic
        messagebox.showinfo("Reset", "Session stats reset!")

if __name__ == "__main__":
    root = tk.Tk()
    gui = KillTrackerGUI(root)
    root.mainloop()
