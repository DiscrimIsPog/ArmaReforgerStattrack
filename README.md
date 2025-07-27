# ARMA StatTrak™ (For CTI_ScoringSystem)
ARMA StatTrak™ is a Python tool that tracks your kills and vehicle kills in Arma Reforger for servers with CTI_ScoringSystem by reading them directly from your game screen. It supports both 1728x1080 and 1920x1080 resolutions. I designed this for OPR fargo servers so others may differ
## Preview

<img width="482" height="161" alt="image" src="https://github.com/user-attachments/assets/f1826817-8072-46aa-9aaa-ce9079478234" />
<img width="602" height="386" alt="image" src="https://github.com/user-attachments/assets/1680c469-c2e9-4c19-93fd-cadd72d586f2" />


## Features

- Tracks kills and vehicle kills in real-time using Tesseract OCR
- Supports two screen resolutions: 1728x1080 and 1920x1080
- Displays current and total stats in a console UI
- Killstreak detection with streak messages
- Persistent stats saved in `data.json`

## Requirements

- Python 3.x
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) (must be installed and left defualt location for it to work)
- Python packages: `pytesseract`, `Pillow`, `pyautogui`
- 

Install dependencies with:
```sh
pip install pytesseract pillow
pip install pyautogui
```

## Usage

1. Install Tesseract OCR and note its installation path.
2. Edit `killtracker.py` and set the correct path for `tesseract_cmd` if needed (its defualt location is already there ignore this if default):
   ```python
   pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
   ```
3. Run the script:
   ```sh
   python killtracker.py
   or open the py file like any other program
   ```
4. Enter your screen resolution when prompted (or press Enter for 1920x1080). (I am not rich :( so i cant calculate 4k or 1440p motitor  cords for the tool)
5. The script will start tracking your kills and vehicle kills. Stats are displayed in the console.

## Files

- [`killtracker.py`](killtracker.py): Main tracking script
- [`data.json`](data.json): Persistent stats storage /  configuration

## Notes

- Only works on Windows.
- Make sure ARMA is running in borderless or windowed mode for accurate OCR.
- Will disapear if you select anything in console, INS fixes it.

## License

MIT License

---

*This project is not affiliated with Bohemia Interactive or ARMA. StatTrak™ is a playful reference to CS:GO weapon counters.*
