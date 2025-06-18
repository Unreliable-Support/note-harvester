# Note Harvester

**Note Harvester** is a powerful desktop utility designed to streamline your information-gathering workflow. With a single global hotkey, you can instantly capture any selected text from any application and save it directly into a designated notebook. Stop the endless cycle of copy-pasting into messy text files and start harvesting information effortlessly.

## 🚀 Quick Demo

Watch a short demonstration to see Note Harvester in action!

[![Note Harvester Demo Video](https://img.youtube.com/vi/z5KpwDU25sY/maxresdefault.jpg)](https://youtu.be/z5KpwDU25sY)

---

## ✨ Features

- **Global Hotkey Capture**: Press `<Ctrl>+<Alt>+A` (or your custom hotkey) anywhere in your OS to save the currently highlighted text.
- **Notebook Organization**: Create, delete, and switch between multiple notebooks to keep your notes organized by topic or project.
- **Robust GUI**:
    - A clean, three-pane view for notebooks, note lists, and detailed note content.
    - **Powerful Filtering**: Search notes by text, source application, and date range (Today, Last 7 Days, etc.).
    - **Note Management**: Merge multiple notes into a single new note, or delete notes individually.
    - **Context Menu**: Right-click on a note to quickly copy its content, source, or timestamp, or to delete it.
- **System Tray Integration**: Minimize the app to the system tray to keep it running unobtrusively in the background.
- **Customizable Hotkey**: Easily change the capture hotkey through the built-in settings window.
- **Crash-Proof Capture**: The hotkey listener is designed to be highly stable, pausing itself during capture to prevent conflicts and ensuring it always restarts.
- **Data Portability**: All notes are stored in human-readable `.json` files, and settings are in a simple `.ini` file, located in your user home folder.

## ⚙️ How It Works

Note Harvester runs a background thread that listens for a global hotkey combination. When the hotkey is pressed:
1.  A "capture" task is sent to the main GUI thread.
2.  The hotkey listener is temporarily **paused** to prevent accidental double-triggers or crashes.
3.  The application programmatically simulates a `Ctrl+C` command to copy the highlighted text.
4.  The clipboard content is retrieved, and the original clipboard content is restored.
5.  The captured text, along with its source application title and timestamp, is saved to the active notebook's JSON file.
6.  The hotkey listener is **resumed**, ready for the next capture.

This pause/resume cycle makes the capture process extremely reliable.

## 🚀 Installation & Usage

This application is built with Python and `tkinter`.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/note-harvester.git
    cd note-harvester
    ```

2.  **Install dependencies:**
    It's recommended to use a virtual environment.
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```
    *You will need to create a `requirements.txt` file with the following content:*
    ```
    pynput
    pygetwindow
    Pillow
    pystray
    pyperclip
    ```

3.  **Run the application:**
    ```bash
    python note-harvester.py
    ```

4.  **How to Use:**
    For a visual guide, [watch the demo on YouTube](https://youtu.be/z5KpwDU25sY).

    - Create or select a notebook from the left panel. This will be your "active" notebook.
    - Go to any other application (browser, PDF reader, code editor).
    - Highlight some text.
    - Press `<Ctrl>+<Alt>+A`.
    - A status message will confirm the note has been saved. The note will appear in the main window.

## 📂 File Structure

- **Notes Data**: Your notes are stored in `C:\Users\YourUser\Note_Harvester_Data\`. Each notebook is a separate `.json` file.
- **Configuration**: The hotkey setting is saved in `config.ini` in the same directory as the script.
- **Crash Log**: If the application crashes, details will be saved to `note_harvester_crash.log`.

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
