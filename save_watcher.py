"""
Background process to monitor Victoria 2 autosave and copy to saves folder.

This module provides automatic save file collection for economic analysis.
While you play Victoria 2, it watches for autosave events and copies each
autosave to the saves folder with a date-based filename.

PURPOSE
=======

Victoria 2 has an autosave feature that creates `autosave.v2` at regular
intervals (configurable in-game, typically monthly or yearly). However,
this file is overwritten each time, losing historical data.

This watcher:
1. Monitors the autosave file for changes
2. Reads the in-game date from the save file
3. Copies the file with a date-based name (e.g., "1836.1.1.txt")
4. Preserves a complete timeline of game states for analysis

HOW IT WORKS
============

```
Victoria 2 Game
       │
       └──> Creates/updates autosave.v2
                   │
                   └──> [watchdog] File system event
                               │
                               └──> AutosaveHandler.on_modified()
                                           │
                                           ├──> Debounce check (2 sec)
                                           │
                                           └──> copy_autosave()
                                                       │
                                                       ├──> Extract date from file
                                                       │
                                                       └──> Copy to saves/YYYY.M.D.txt
```

USAGE
=====

1. Start the watcher before beginning your Victoria 2 session:
   $ python save_watcher.py

2. Play Victoria 2 with autosave enabled

3. Stop the watcher with Ctrl+C when done

4. Process collected saves:
   $ python process_saves.py

FILE LOCATIONS
==============

Input (autosave location):
    %USERPROFILE%/Documents/Paradox Interactive/Victoria II/save games/autosave.v2

Output:
    saves/1836.1.1.txt
    saves/1836.2.1.txt
    saves/1836.3.1.txt
    ...

REQUIREMENTS
============

- watchdog package: pip install watchdog
- Victoria 2 installed with autosave enabled
- Python 3.9+ (for Path and type hints)

AUTOSAVE CONFIGURATION
======================

In Victoria 2, go to Settings and configure autosave:
- Autosave: Monthly (recommended for detailed analysis)
- Or: Yearly (for longer games with less granularity)

Monthly autosaves create ~1200 data points for a full 1836-1936 game.

Author: Victoria 2 Economy Analysis Tool Project
"""

import os
import shutil
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


# =============================================================================
# PATH CONFIGURATION
# =============================================================================

# Victoria 2 default save game location on Windows
# The game uses the user's Documents folder, not the game installation directory
VIC2_SAVE_DIR = Path(os.environ["USERPROFILE"]) / "Documents" / "Paradox Interactive" / "Victoria II" / "save games"

# The autosave file that Victoria 2 creates
# This is overwritten each autosave cycle
AUTOSAVE_FILE = VIC2_SAVE_DIR / "autosave.v2"

# Local directory where we store collected saves
# Each autosave is copied here with a date-based filename
OUTPUT_DIR = Path(__file__).parent / "saves"


# =============================================================================
# SAVE FILE PROCESSING
# =============================================================================

def extract_date_from_save(file_path: Path) -> str:
    """
    Extract the in-game date from the first line of a save file.

    Victoria 2 save files always start with a date= line:
        date="1836.1.1"

    Args:
        file_path: Path to the save file

    Returns:
        str: The in-game date in "YYYY.M.D" format

    Raises:
        ValueError: If the date cannot be extracted (malformed file)

    Example:
        >>> extract_date_from_save(Path("autosave.v2"))
        "1850.6.15"

    Note:
        Uses Latin-1 encoding, which is standard for Paradox games.
    """
    with open(file_path, "r", encoding="latin-1") as f:
        first_line = f.readline().strip()

    # Expected format: date="yyyy.mm.dd"
    if first_line.startswith("date="):
        date_value = first_line[5:]  # Remove "date=" prefix
        return date_value.strip('"')  # Remove surrounding quotes

    raise ValueError(f"Could not extract date from save file: {first_line}")


def copy_autosave():
    """
    Copy autosave.v2 to saves folder with date-based name.

    This is the main action function called when an autosave event is detected.
    It:
    1. Checks if autosave file exists
    2. Extracts the in-game date
    3. Copies the file with the date as filename

    Output Filename Format:
        saves/YYYY.M.D.txt

    Examples:
        autosave.v2 with date="1836.1.1" → saves/1836.1.1.txt
        autosave.v2 with date="1850.12.15" → saves/1850.12.15.txt

    Note:
        Uses shutil.copy2 to preserve file metadata (timestamps).
        The .txt extension is used for easier handling in later processing.
    """
    if not AUTOSAVE_FILE.exists():
        print(f"Autosave file not found: {AUTOSAVE_FILE}")
        return

    try:
        # Extract in-game date to use as filename
        game_date = extract_date_from_save(AUTOSAVE_FILE)
        output_file = OUTPUT_DIR / f"{game_date}.txt"

        # Copy the file (copy2 preserves metadata)
        shutil.copy2(AUTOSAVE_FILE, output_file)
        print(f"Copied autosave to: {output_file}")

    except Exception as e:
        print(f"Error copying autosave: {e}")


# =============================================================================
# FILE SYSTEM WATCHER
# =============================================================================

class AutosaveHandler(FileSystemEventHandler):
    """
    Handler for autosave file modifications.

    This class uses the watchdog library to receive file system events.
    When the autosave file is modified, it triggers a copy operation.

    Attributes:
        last_modified (float): Timestamp of last processed modification
        debounce_seconds (float): Minimum time between processing events

    Debouncing:
        File system events can fire multiple times for a single logical
        save operation. The debounce mechanism ignores rapid-fire events
        within the debounce window (default: 2 seconds).

    Event Flow:
        on_modified() → debounce check → copy_autosave()

    Example Usage:
        handler = AutosaveHandler()
        observer = Observer()
        observer.schedule(handler, watch_directory, recursive=False)
        observer.start()
    """

    def __init__(self):
        """Initialize the handler with debounce tracking."""
        self.last_modified = 0
        # Debounce threshold in seconds
        # Victoria 2 may trigger multiple file system events during save
        self.debounce_seconds = 2

    def on_modified(self, event):
        """
        Handle file modification events.

        Called by watchdog when any file in the watched directory changes.
        Filters for autosave.v2 and applies debouncing.

        Args:
            event: FileSystemEvent with src_path and is_directory attributes

        Processing:
            1. Ignore directory events
            2. Check if the modified file is autosave.v2
            3. Apply debounce (ignore if too recent)
            4. Trigger copy operation
        """
        # Ignore directory events
        if event.is_directory:
            return

        # Check if it's the autosave file (case-insensitive)
        if Path(event.src_path).name.lower() == "autosave.v2":
            current_time = time.time()

            # Debounce: ignore if triggered too recently
            # This prevents duplicate processing when the OS fires
            # multiple events for a single file write
            if current_time - self.last_modified < self.debounce_seconds:
                return

            self.last_modified = current_time
            print(f"\nAutosave modified at {time.strftime('%H:%M:%S')}")
            copy_autosave()


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main():
    """
    Main entry point for the save watcher.

    Sets up the file system observer and runs until interrupted with Ctrl+C.

    Setup Steps:
        1. Create output directory if needed
        2. Verify Victoria 2 save directory exists
        3. Start file system observer
        4. Wait for events (Ctrl+C to stop)
        5. Clean shutdown

    Expected Console Output:
        Watching for autosave changes in: C:/Users/.../save games
        Saving copies to: .../saves
        Press Ctrl+C to stop.

        Autosave modified at 14:30:25
        Copied autosave to: .../saves/1850.1.1.txt

    Error Handling:
        - Prints error if Victoria 2 save directory not found
        - Gracefully handles Ctrl+C for clean shutdown
    """
    # Create output directory if it doesn't exist
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Verify Victoria 2 is installed and has created save files
    if not VIC2_SAVE_DIR.exists():
        print(f"Victoria 2 save directory not found: {VIC2_SAVE_DIR}")
        print("Please check that Victoria 2 is installed and has created save files.")
        return

    print(f"Watching for autosave changes in: {VIC2_SAVE_DIR}")
    print(f"Saving copies to: {OUTPUT_DIR}")
    print("Press Ctrl+C to stop.\n")

    # Set up the file system observer
    event_handler = AutosaveHandler()
    observer = Observer()
    # Watch only the save games directory (not recursive)
    observer.schedule(event_handler, str(VIC2_SAVE_DIR), recursive=False)
    observer.start()

    # Run until Ctrl+C
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping watcher...")
        observer.stop()

    # Wait for observer thread to finish
    observer.join()
    print("Watcher stopped.")


if __name__ == "__main__":
    main()
