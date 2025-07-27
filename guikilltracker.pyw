import tkinter as tk
from tkinter import ttk
import threading
import time
import pytesseract
from PIL import ImageGrab
import re
import json
import os
from datetime import datetime, timedelta
import sys
import keyboard

# Set the path to the Tesseract executable (required for OCR)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Define screen regions for OCR for 1728x1080 resolution
REGION_KILLS_1728 = (1300, 800, 1431, 825)
REGION_VEHICLE_KILLS_1728 = (1300, 830, 1470, 855)

# Define screen regions for OCR for 1920x1080 resolution
REGION_KILLS_1920 = (1440, 830, 1525, 860)
REGION_VEHICLE_KILLS_1920 = (1440, 860, 1600, 890)

# JSON file to store persistent stats
LOG_FILE = "data.json"

def prompt_screen_resolution():
    """
    Prompt user for screen resolution and validate input.
    Only allows 1728x1080 or 1920x1080.
    """
    print("Enter your screen resolution (only 1728x1080 or 1920x1080 supported):")
    user_input = input("Resolution: ").strip()

    if user_input == "":
        return 1920, 1080

    try:
        width, height = map(int, user_input.lower().split('x'))
        if (width, height) not in [(1728, 1080), (1920, 1080)]:
            print("❌ Unsupported resolution! Only 1728x1080 or 1920x1080 allowed.")
            sys.exit(1)
        return width, height
    except:
        print("Invalid input. Exiting.")
        sys.exit(1)

def extract_stat(text):
    """
    Extract the first integer found in a string.
    Used to parse kill counts from OCR text.
    """
    match = re.search(r'([0-9]+)', text)
    return int(match.group(1)) if match else None

def get_text_with_confidence(img):
    """
    Run OCR on an image and return the combined text and median confidence.
    """
    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
    texts = data['text']
    confs = data['conf']

    combined_text = ''
    conf_values = []

    for i, text in enumerate(texts):
        if text.strip() != '':
            combined_text += text.strip()
            try:
                conf = int(confs[i])
                conf_values.append(conf)
            except:
                pass

    if conf_values:
        conf_values_sorted = sorted(conf_values)
        median_conf = conf_values_sorted[len(conf_values_sorted)//2]
    else:
        median_conf = 0

    return combined_text, median_conf

def get_streak_message(count):
    """
    Return a message based on the current killstreak count.
    """
    if count <= 1:
        return "You got a kill! 💥🔫"
    elif count == 2:
        return "Double Kill 🔥"
    elif count == 3:
        return "Triple Kill 🔥🔥"
    elif count == 4:
        return "Quadra Kill 🔥🔥🔥"
    elif count == 5:
        return "Penta Kill 🔥🔥🔥🔥"
    else:
        return f"🔥 {count} Kill Streak! 🔥🔥🔥"

def load_config():
    """
    Load stats and resolution from the config file.
    If the file doesn't exist, create it with default values.
    """
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            data = json.load(f)
            kills = data.get("kills", 0)
            vehicle_kills = data.get("vehicle_kills", 0)
            resolution = data.get("resolution", None)
            return kills, vehicle_kills, resolution
    else:
        print("Creating config... 🛠️")
        with open(LOG_FILE, "w") as f:
            json.dump({"kills": 0, "vehicle_kills": 0}, f)
        return 0, 0, None

def save_config(kills_total, vehicle_kills_total, resolution=None):
    """
    Save stats and optionally resolution to the config file.
    """
    config = {
        "kills": kills_total,
        "vehicle_kills": vehicle_kills_total
    }
    if resolution:
        config["resolution"] = resolution
    with open(LOG_FILE, "w") as f:
        json.dump(config, f)

class ConsoleStyleGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("ARMA StatTrak™")
        self.root.geometry("600x350")  # Increased window size
        self.root.configure(bg='#0d1b2a')
        
        # Tracking enabled/disabled state
        self.tracking_enabled = True
        
        # Initialize tracking variables
        self.total_kills, self.total_vehicle_kills, self.saved_resolution = load_config()
        
        # Use saved resolution if available, otherwise prompt user
        if self.saved_resolution:
            self.actual_width, self.actual_height = self.saved_resolution
            if (self.actual_width, self.actual_height) not in [(1728, 1080), (1920, 1080)]:
                print("❌ Incompatible resolution saved in config! Please delete the config file and restart.")
                sys.exit(1)
        else:
            self.actual_width, self.actual_height = prompt_screen_resolution()
            save_config(self.total_kills, self.total_vehicle_kills, (self.actual_width, self.actual_height))

        # Set OCR regions based on resolution
        if (self.actual_width, self.actual_height) == (1728, 1080):
            self.REGION_KILLS = REGION_KILLS_1728
            self.REGION_VEHICLE_KILLS = REGION_VEHICLE_KILLS_1728
        elif (self.actual_width, self.actual_height) == (1920, 1080):
            self.REGION_KILLS = REGION_KILLS_1920
            self.REGION_VEHICLE_KILLS = REGION_VEHICLE_KILLS_1920
        else:
            print("❌ Unsupported resolution! Exiting.")
            sys.exit(1)

        # Tracking variables
        self.last_kills = None
        self.last_vehicle_kills = None
        self.current_game_kills = 0
        self.current_game_vehicle_kills = 0
        self.streak_kills = 0
        
        self.streak_start = None
        self.kill_streak_count = 0
        self.streak_message = ""
        self.streak_expire = None
        
        self.last_streak_kill_count = None
        self.last_streak_vehicle_kill_count = None
        
        # Stats variables for GUI
        self.kills = tk.StringVar(value=str(self.current_game_kills))
        self.total_kills_var = tk.StringVar(value=str(self.total_kills))
        self.vehicle_kills = tk.StringVar(value=str(self.current_game_vehicle_kills))
        self.total_vehicle_kills_var = tk.StringVar(value=str(self.total_vehicle_kills))
        self.streak_kills_var = tk.StringVar(value=str(self.streak_kills))
        self.total_combined = tk.StringVar(value=str(self.total_kills + self.total_vehicle_kills))
        self.message = tk.StringVar(value="")
        
        self.setup_ui()
        
        # Set up keyboard hook for F6
        keyboard.add_hotkey('f6', self.toggle_tracking)
        
        # Start tracking in a separate thread
        self.tracking_thread = threading.Thread(target=self.track_kills, daemon=True)
        self.tracking_thread.start()
        
    def setup_ui(self):
        # Header
        header_frame = tk.Frame(self.root, bg='#0d1b2a', height=40)  # Reduced from 50 to 40
        header_frame.pack(fill='x', pady=(8, 3))  # Reduced top padding from 10 to 8
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(header_frame, text="ARMA STATTRACK™", 
                              fg='#e0e1dd', bg='#0d1b2a', 
                              font=('dixplay', 16, 'bold'))  # Title stays 16
        title_label.pack()
        
        # Separator line
        separator = tk.Frame(self.root, bg='#778da9', height=2)
        separator.pack(fill='x', padx=30, pady=(0, 8))  # Reduced bottom padding from 10 to 8
        
        # Main content area
        content_frame = tk.Frame(self.root, bg='#0d1b2a')
        content_frame.pack(fill='both', expand=True, padx=20, pady=(0, 10))  # Reduced bottom padding from 15 to 10
        
        # Top row - Current and Total stats
        top_frame = tk.Frame(content_frame, bg='#0d1b2a')
        top_frame.pack(fill='x', pady=(0, 8))
        
        # Left panel - Current stats
        left_panel = tk.Frame(top_frame, bg='#1b263b', relief='raised', bd=3, highlightbackground='#778da9', highlightthickness=2)
        left_panel.pack(side='left', fill='both', expand=True, padx=(0, 8))
        
        current_header = tk.Label(left_panel, text="CURRENT", 
                                 fg='#e0e1dd', bg='#1b263b', 
                                 font=('dixplay', 11, 'bold', 'underline'))  # Subtitle stays 11
        current_header.pack(pady=(8, 8))
        
        self.kills_current = tk.Label(left_panel, text="Kills: 0", 
                                     fg='#e0e1dd', bg='#1b263b', 
                                     font=('dixplay', 17, 'bold'))  # 13 + 4 = 17
        self.kills_current.pack(pady=3)
        
        self.vehicle_current = tk.Label(left_panel, text="Vehicle: 0", 
                                       fg='#e0e1dd', bg='#1b263b', 
                                       font=('dixplay', 17, 'bold'))  # 13 + 4 = 17
        self.vehicle_current.pack(pady=3)
        
        self.streak_current = tk.Label(left_panel, text="Streak: 0", 
                                      fg='#e0e1dd', bg='#1b263b', 
                                      font=('dixplay', 17, 'bold'))  # 13 + 4 = 17
        self.streak_current.pack(pady=(3, 8))
        
        # Middle panel - Total stats
        middle_panel = tk.Frame(top_frame, bg='#1b263b', relief='raised', bd=3, highlightbackground='#778da9', highlightthickness=2)
        middle_panel.pack(side='left', fill='both', expand=True, padx=4)
        
        total_header = tk.Label(middle_panel, text="TOTAL", 
                               fg='#e0e1dd', bg='#1b263b', 
                               font=('dixplay', 11, 'bold', 'underline'))  # Subtitle stays 11
        total_header.pack(pady=(8, 8))
        
        self.kills_total = tk.Label(middle_panel, text="Kills: 0", 
                                   fg='#e0e1dd', bg='#1b263b', 
                                   font=('dixplay', 17, 'bold'))  # 13 + 4 = 17
        self.kills_total.pack(pady=3)
        
        self.vehicle_total = tk.Label(middle_panel, text="Vehicle: 0", 
                                     fg='#e0e1dd', bg='#1b263b', 
                                     font=('dixplay', 17, 'bold'))  # 13 + 4 = 17
        self.vehicle_total.pack(pady=3)
        
        self.combined_total = tk.Label(middle_panel, text="Combined: 0", 
                                      fg='#e0e1dd', bg='#1b263b', 
                                      font=('dixplay', 17, 'bold'))  # 13 + 4 = 17
        self.combined_total.pack(pady=(3, 8))
        
        # Right panel - Status
        right_panel = tk.Frame(top_frame, bg='#1b263b', relief='raised', bd=3, highlightbackground='#778da9', highlightthickness=2)
        right_panel.pack(side='right', fill='both', expand=True, padx=(8, 0))
        
        status_header = tk.Label(right_panel, text="STATUS", 
                                fg='#e0e1dd', bg='#1b263b', 
                                font=('dixplay', 11, 'bold', 'underline'))  # Subtitle stays 11
        status_header.pack(pady=(8, 5))
        
        self.status_text = tk.Label(right_panel, text="Loading...", 
                                   fg='#e0e1dd', bg='#1b263b', 
                                   font=('dixplay', 15, 'bold'),  # 11 + 4 = 15
                                   justify='left')
        self.status_text.pack(pady=3)
        
        # F6 info
        self.f6_info = tk.Label(right_panel, text="[F6] ON", 
                               fg='#00ff00', bg='#1b263b', 
                               font=('dixplay', 16, 'bold'))  # 12 + 4 = 16
        self.f6_info.pack(pady=(3, 8))
        
        # Bottom row - Output panel
        output_panel = tk.Frame(content_frame, bg='#1b263b', relief='raised', bd=3, highlightbackground='#778da9', highlightthickness=2)
        output_panel.pack(fill='both', expand=True, pady=(8, 0))
        
        output_header = tk.Label(output_panel, text="OUTPUT", 
                                fg='#e0e1dd', bg='#1b263b', 
                                font=('dixplay', 11, 'bold', 'underline'))  # Subtitle stays 11
        output_header.pack(pady=(8, 5))
        
        # Output text area
        self.output_text = tk.Label(output_panel, text="Waiting for kills...", 
                                   fg='#e0e1dd', bg='#1b263b', 
                                   font=('dixplay', 17, 'bold'),  # 13 + 4 = 17
                                   justify='center',
                                   wraplength=500)
        self.output_text.pack(pady=(5, 8), expand=True)
        
        # Update display initially
        self.update_display()

    def toggle_tracking(self):
        """
        Toggle tracking on/off with F6 key
        """
        self.tracking_enabled = not self.tracking_enabled
        self.update_status_display()
        
    def update_status_display(self):
        """
        Update the F6 toggle status
        """
        if self.tracking_enabled:
            self.f6_info.config(text="[F6] ON", fg='#00ff00')
        else:
            self.f6_info.config(text="[F6] OFF", fg='#ff0000')
        
    def update_display(self):
        # Update current stats
        self.kills_current.config(text=f"Kills: {self.kills.get()}")
        self.vehicle_current.config(text=f"Vehicle: {self.vehicle_kills.get()}")
        self.streak_current.config(text=f"Streak: {self.streak_kills_var.get()}")
        
        # Update total stats
        self.kills_total.config(text=f"Kills: {self.total_kills_var.get()}")
        self.vehicle_total.config(text=f"Vehicle: {self.total_vehicle_kills_var.get()}")
        self.combined_total.config(text=f"Combined: {self.total_combined.get()}")
        
        # Update status
        if self.tracking_enabled:
            status_msg = f"Tracking: ON\nRes: {self.actual_width}x{self.actual_height}"
        else:
            status_msg = f"Tracking: OFF\nRes: {self.actual_width}x{self.actual_height}"
        
        self.status_text.config(text=status_msg)
        
        # Update output with killstreak message
        msg = self.message.get()
        if msg:
            self.output_text.config(text=msg)
        else:
            self.output_text.config(text="Waiting for kills...")
        
        # Update F6 status
        self.update_status_display()

    def track_kills(self):
        """
        Main tracking loop that runs in a separate thread
        """
        print(f"Using resolution: {self.actual_width}x{self.actual_height}")
        print("Tracking started 🔍🎯")
        print("Press F6 to toggle tracking on/off")
        time.sleep(2)
        
        # Update initial status
        self.root.after(0, self.update_status_display)
        
        while True:
            # Only track if enabled
            if self.tracking_enabled:
                got_kill = False
                got_vehicle_kill = False
                now = datetime.now()

                # Expire streak if time runs out
                if self.streak_expire and now >= self.streak_expire:
                    self.streak_message = ""
                    self.kill_streak_count = 0
                    self.streak_start = None
                    self.streak_expire = None
                    self.streak_kills = 0
                    
                # Grab and OCR the kills region
                img_k = ImageGrab.grab(bbox=self.REGION_KILLS)
                text_k, conf_k = get_text_with_confidence(img_k)
                kills = extract_stat(text_k) if conf_k >= 88 else None

                # Grab and OCR the vehicle kills region
                img_vk = ImageGrab.grab(bbox=self.REGION_VEHICLE_KILLS)
                text_vk, conf_vk = get_text_with_confidence(img_vk)
                vehicle_kills = extract_stat(text_vk) if conf_vk >= 88 else None

                # Update kill stats and detect kill events
                if kills is not None:
                    if self.last_kills is None:
                        self.last_kills = kills
                        self.current_game_kills = kills
                    elif kills < self.last_kills:
                        # Counter reset (new game), add to total and reset current
                        self.total_kills += kills
                        self.current_game_kills = kills
                        self.last_kills = kills
                        got_kill = True
                    elif kills > self.last_kills:
                        # Increment detected
                        diff = kills - self.last_kills
                        self.current_game_kills += diff
                        self.total_kills += diff
                        self.last_kills = kills
                        got_kill = True

                # Update vehicle kill stats and detect vehicle kill events
                if vehicle_kills is not None:
                    if self.last_vehicle_kills is None:
                        self.last_vehicle_kills = vehicle_kills
                        self.current_game_vehicle_kills = vehicle_kills
                    elif vehicle_kills < self.last_vehicle_kills:
                        # Vehicle kill counter reset (game ended) — do NOT add to total
                        self.current_game_vehicle_kills = vehicle_kills
                        self.last_vehicle_kills = vehicle_kills
                    elif vehicle_kills > self.last_vehicle_kills:
                        diff = vehicle_kills - self.last_vehicle_kills
                        self.current_game_vehicle_kills += diff
                        self.total_vehicle_kills += diff
                        self.last_vehicle_kills = vehicle_kills
                        got_vehicle_kill = True

                # Handle streak logic
                if got_kill or got_vehicle_kill:
                    # Start new streak if expired or not started
                    if not self.streak_start or (now - self.streak_start).total_seconds() > 30:
                        self.streak_start = now
                        self.streak_expire = now + timedelta(seconds=30)
                        self.kill_streak_count = 0
                        self.streak_kills = 0
                        self.last_streak_kill_count = kills
                        self.last_streak_vehicle_kill_count = vehicle_kills

                    increment = 0
                    if got_kill and self.last_streak_kill_count is not None:
                        increment += kills - self.last_streak_kill_count
                        self.last_streak_kill_count = kills

                    if got_vehicle_kill and self.last_streak_vehicle_kill_count is not None:
                        increment += vehicle_kills - self.last_streak_vehicle_kill_count
                        self.last_streak_vehicle_kill_count = vehicle_kills

                    if increment > 0:
                        self.kill_streak_count += increment
                        self.streak_kills += increment
                        self.streak_message = get_streak_message(self.kill_streak_count)
                        self.streak_expire = now + timedelta(seconds=30)

                    save_config(self.total_kills, self.total_vehicle_kills, (self.actual_width, self.actual_height))

                # Update GUI variables
                self.root.after(0, self.update_gui_vars)
            
            time.sleep(1)
    
    def update_gui_vars(self):
        """
        Update GUI variables and display (must run on main thread)
        """
        self.kills.set(str(self.current_game_kills))
        self.total_kills_var.set(str(self.total_kills))
        self.vehicle_kills.set(str(self.current_game_vehicle_kills))
        self.total_vehicle_kills_var.set(str(self.total_vehicle_kills))
        self.streak_kills_var.set(str(self.streak_kills))
        self.total_combined.set(str(self.total_kills + self.total_vehicle_kills))
        
        if self.streak_message:
            self.message.set(self.streak_message)
        else:
            self.message.set("")
        
        self.update_display()

        if self.streak_message:
            self.message.set(self.streak_message)
        else:
            self.message.set("")
        
        self.update_display()
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    gui = ConsoleStyleGUI()
    gui.run()