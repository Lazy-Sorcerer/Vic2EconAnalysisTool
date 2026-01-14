"""
Background process to monitor Victoria 2 autosave and copy to saves folder.
Renames files based on in-game date from the save file.
"""

import os
import shutil
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


# Paths
VIC2_SAVE_DIR = Path(os.environ["USERPROFILE"]) / "Documents" / "Paradox Interactive" / "Victoria II" / "save games"
AUTOSAVE_FILE = VIC2_SAVE_DIR / "autosave.v2"
OUTPUT_DIR = Path(__file__).parent / "saves"


def extract_date_from_save(file_path: Path) -> str:
    """Extract the in-game date from the first line of a save file."""
    with open(file_path, "r", encoding="latin-1") as f:
        first_line = f.readline().strip()

    # First line format: date="yyyy.mm.dd"
    if first_line.startswith("date="):
        date_value = first_line[5:]  # Remove "date=" prefix
        return date_value.strip('"')  # Remove surrounding quotes

    raise ValueError(f"Could not extract date from save file: {first_line}")


def copy_autosave():
    """Copy autosave.v2 to saves folder with date-based name."""
    if not AUTOSAVE_FILE.exists():
        print(f"Autosave file not found: {AUTOSAVE_FILE}")
        return

    try:
        game_date = extract_date_from_save(AUTOSAVE_FILE)
        output_file = OUTPUT_DIR / f"{game_date}.txt"

        # Copy the file
        shutil.copy2(AUTOSAVE_FILE, output_file)
        print(f"Copied autosave to: {output_file}")

    except Exception as e:
        print(f"Error copying autosave: {e}")


class AutosaveHandler(FileSystemEventHandler):
    """Handler for autosave file modifications."""

    def __init__(self):
        self.last_modified = 0
        # Debounce threshold in seconds (avoid duplicate triggers)
        self.debounce_seconds = 2

    def on_modified(self, event):
        if event.is_directory:
            return

        # Check if it's the autosave file
        if Path(event.src_path).name.lower() == "autosave.v2":
            current_time = time.time()

            # Debounce: ignore if triggered too recently
            if current_time - self.last_modified < self.debounce_seconds:
                return

            self.last_modified = current_time
            print(f"\nAutosave modified at {time.strftime('%H:%M:%S')}")
            copy_autosave()


def main():
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Check if Victoria 2 save directory exists
    if not VIC2_SAVE_DIR.exists():
        print(f"Victoria 2 save directory not found: {VIC2_SAVE_DIR}")
        print("Please check that Victoria 2 is installed and has created save files.")
        return

    print(f"Watching for autosave changes in: {VIC2_SAVE_DIR}")
    print(f"Saving copies to: {OUTPUT_DIR}")
    print("Press Ctrl+C to stop.\n")

    event_handler = AutosaveHandler()
    observer = Observer()
    observer.schedule(event_handler, str(VIC2_SAVE_DIR), recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping watcher...")
        observer.stop()

    observer.join()
    print("Watcher stopped.")


if __name__ == "__main__":
    main()
