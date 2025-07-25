import pytesseract
from PIL import ImageGrab
import time
import re
import json
import os
from datetime import datetime, timedelta
import sys

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

def print_box(kills, total_kills, vehicle_kills, total_vehicle_kills, streak_kills, total_combined_kills, message=""):
    """
    Print a formatted stats box to the console, including current and total stats.
    Optionally display a message (e.g., killstreak).
    """
    print("\033c", end="")  # Clear console
    print("╔═════════════════════ ARMA StatTrak™ ═════════════════════╗")
    print("║                   Current        |         Total         ║")
    print("╠══════════════════════════════════════════════════════════╣")
    print(f"║ Kills:           {kills:<10} |       {total_kills:<13} ║")
    print(f"║ Vehicle Kills:   {vehicle_kills:<10} |       {total_vehicle_kills:<13} ║")
    print(f"║ Killstreak:      {streak_kills:<10} |       {total_combined_kills:<13} ║")
    print("╚══════════════════════════════════════════════════════════╝")
    if message:
        print(f"💬 {message}")

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

def main():
    """
    Main loop: tracks kills and vehicle kills using OCR, manages streaks,
    updates stats, and prints the stats box.
    """
    total_kills, total_vehicle_kills, saved_resolution = load_config()

    # Use saved resolution if available, otherwise prompt user
    if saved_resolution:
        actual_width, actual_height = saved_resolution
        if (actual_width, actual_height) not in [(1728, 1080), (1920, 1080)]:
            print("❌ Incompatible resolution saved in config! Please delete the config file and restart.")
            sys.exit(1)
    else:
        actual_width, actual_height = prompt_screen_resolution()
        save_config(total_kills, total_vehicle_kills, (actual_width, actual_height))

    # Set OCR regions based on resolution
    if (actual_width, actual_height) == (1728, 1080):
        REGION_KILLS = REGION_KILLS_1728
        REGION_VEHICLE_KILLS = REGION_VEHICLE_KILLS_1728
    elif (actual_width, actual_height) == (1920, 1080):
        REGION_KILLS = REGION_KILLS_1920
        REGION_VEHICLE_KILLS = REGION_VEHICLE_KILLS_1920
    else:
        print("❌ Unsupported resolution! Exiting.")
        sys.exit(1)

    print(f"Using resolution: {actual_width}x{actual_height}")
    print("Tracking started 🔍🎯")
    time.sleep(2)

    # Initialize tracking variables
    last_kills = None
    last_vehicle_kills = None
    current_game_kills = 0
    current_game_vehicle_kills = 0
    streak_kills = 0

    streak_start = None
    kill_streak_count = 0
    streak_message = ""
    streak_expire = None

    last_streak_kill_count = None
    last_streak_vehicle_kill_count = None

    while True:
        got_kill = False
        got_vehicle_kill = False
        now = datetime.now()

        # Expire streak if time runs out
        if streak_expire and now >= streak_expire:
            streak_message = ""
            kill_streak_count = 0
            streak_start = None
            streak_expire = None
            streak_kills = 0
            
        # Grab and OCR the kills region
        img_k = ImageGrab.grab(bbox=REGION_KILLS)
        #img_k.save("kills.png") # Uncomment to save screenshot for debugging
        text_k, conf_k = get_text_with_confidence(img_k)
        kills = extract_stat(text_k) if conf_k >= 88 else None

        # Grab and OCR the vehicle kills region
        img_vk = ImageGrab.grab(bbox=REGION_VEHICLE_KILLS)
        #img_vk.save("vehicle.png") # Uncomment to save screenshot for debugging
        text_vk, conf_vk = get_text_with_confidence(img_vk)
        vehicle_kills = extract_stat(text_vk) if conf_vk >= 88 else None

        # Update kill stats and detect kill events
        if kills is not None:
            if last_kills is None:
                last_kills = kills
                current_game_kills = kills
            elif kills < last_kills:
                # Counter reset (new game), add to total and reset current
                total_kills += kills
                current_game_kills = kills
                last_kills = kills
                got_kill = True
            elif kills > last_kills:
                # Increment detected
                diff = kills - last_kills
                current_game_kills += diff
                total_kills += diff
                last_kills = kills
                got_kill = True

        # Update vehicle kill stats and detect vehicle kill events
        if vehicle_kills is not None:
            if last_vehicle_kills is None:
                last_vehicle_kills = vehicle_kills
                current_game_vehicle_kills = vehicle_kills
            elif vehicle_kills < last_vehicle_kills:
                # Vehicle kill counter reset (game ended) — do NOT add to total
                current_game_vehicle_kills = vehicle_kills
                last_vehicle_kills = vehicle_kills
            elif vehicle_kills > last_vehicle_kills:
                diff = vehicle_kills - last_vehicle_kills
                current_game_vehicle_kills += diff
                total_vehicle_kills += diff
                last_vehicle_kills = vehicle_kills
                got_vehicle_kill = True

        # Handle streak logic
        if got_kill or got_vehicle_kill:
            # Start new streak if expired or not started
            if not streak_start or (now - streak_start).total_seconds() > 30:
                streak_start = now
                streak_expire = now + timedelta(seconds=30)
                kill_streak_count = 0
                streak_kills = 0
                last_streak_kill_count = kills
                last_streak_vehicle_kill_count = vehicle_kills

            increment = 0
            if got_kill and last_streak_kill_count is not None:
                increment += kills - last_streak_kill_count
                last_streak_kill_count = kills

            if got_vehicle_kill and last_streak_vehicle_kill_count is not None:
                increment += vehicle_kills - last_streak_vehicle_kill_count
                last_streak_vehicle_kill_count = vehicle_kills

            if increment > 0:
                kill_streak_count += increment
                streak_kills += increment
                streak_message = get_streak_message(kill_streak_count)
                streak_expire = now + timedelta(seconds=30)

            save_config(total_kills, total_vehicle_kills, (actual_width, actual_height))

        # Print stats box
        total_combined_kills = total_kills + total_vehicle_kills
        print_box(current_game_kills, total_kills, current_game_vehicle_kills, total_vehicle_kills, streak_kills, total_combined_kills, streak_message)
        time.sleep(1)

if __name__ == "__main__":
    main()
