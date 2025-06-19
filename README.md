# Note Harvester

**Note Harvester** is a powerful yet lightweight desktop utility designed to streamline your information-gathering workflow. With a single, customizable global hotkey, you can instantly capture any selected text from any application and save it directly into an organized notebook, automatically tracking its source. Stop the endless cycle of copy-pasting into messy text files and never lose a piece of information again.

[![Note Harvester Demo](https://img.youtube.com/vi/z5KpwDU25sY/maxresdefault.jpg)](https://youtu.be/z5KpwDU25sY)
*(Click the image to watch the demo on YouTube)*

## 🚀 Getting Started (Recommended for Windows Users)

The easiest way to get started is by using the pre-compiled application. No installation is required.

1.  **[Go to the Releases Page](https://github.com/Unreliable-Support/note-harvester/releases)**.
2.  Under the latest release, download the `NoteHarvester.exe` file.
3.  Save the file anywhere on your computer (e.g., your Desktop) and double-click to run it.

> **Note:** When you first run the `.exe`, Windows Defender SmartScreen might show a warning because the application is not code-signed. This is normal. You can bypass this by clicking **"More info"** and then **"Run anyway"**.

## ✨ Core Features

-   **Global Hotkey Capture**: Select text in any application and press a customizable hotkey (`<Ctrl>+B` by default) to instantly save it.
-   **Automatic Source Tracking**: Automatically records the title of the window you captured from as the note's "source".
-   **Notebook Organization**: Organize your notes into separate notebooks, which are stored as simple, portable JSON files.
-   **Powerful Filtering & Search**:
    -   Full-text search with case-sensitive and whole-word options.
    -   Filter notes by their source application/document.
    -   Filter notes by a specific date range.
-   **Advanced Note Management**:
    -   Merge multiple selected notes into a single new note.
    -   **Merge by Source**: A powerful feature to combine all notes from a specific source (e.g., a single PDF or webpage) into one consolidated document.
    -   Right-click context menu for quick actions like copying content or deleting.
-   **Flexible Viewing**:
    -   A "Single Page View" to read all notes in a notebook like a continuous document.
    -   Zoom in and out (`Ctrl` + `Mouse Wheel`) for comfortable reading in both the detail pane and single-page view.
    -   Toggleable note detail pane to maximize list visibility.
-   **Export Your Data**:
    -   Export your notebooks to clean, professional-looking **PDF** or **HTML** files using Pandoc.
-   **System Tray Integration**: Minimize the application to your system tray to keep it running unobtrusively in the background.

## 👨‍💻 Running from Source (Advanced Method)

If you prefer to run the application directly from the Python source code, follow these steps.

### Prerequisites

1.  **Python 3.x**: Ensure you have Python installed.
2.  **Pandoc (for Exporting)**: To use the PDF/HTML export feature, you must install Pandoc. You can find instructions at [pandoc.org/installing](https://pandoc.org/installing.html).
3.  **LaTeX (for PDF Export)**: For PDF exporting, Pandoc requires a LaTeX distribution.
    -   **Windows**: [MiKTeX](https://miktex.org/download)
    -   **macOS**: [MacTeX](https://www.tug.org/mactex/)
    -   **Linux**: TeX Live (`sudo apt-get install texlive-latex-base` on Debian/Ubuntu).

### Setup Steps

1.  **Clone or Download the Repository**:
    Download or clone all files from this repository to a local folder.

2.  **Install Required Python Packages**:
    Open a terminal or command prompt in the project folder and run the following command:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the Application**:
    With your terminal still in the project folder, run the script:
    ```bash
    python note-harvester.py
    ```

## How to Use

### First Launch

-   On the first run, the app will automatically create:
    -   A `config.ini` file in the same directory to store your hotkey settings.
    -   A `Note_Harvester_Data` folder in your user's home directory (`C:\Users\YourName` on Windows or `/home/yourname` on Linux) to store your notebooks.

### Capturing Your First Note

1.  **Create a Notebook**: Click the "New" button in the left-hand "Notebooks" panel and give your notebook a name (e.g., "Research"). The new notebook will be selected automatically.
2.  **Select Text**: Go to any other application (a web browser, a PDF reader, a code editor) and highlight some text.
3.  **Press the Hotkey**: Press **`<Ctrl> + B`**.
4.  **Done!**: The selected text, along with the title of the source window, has been instantly saved to your active notebook. The main window will refresh to show your new note at the top of the list.

### Navigating the Interface

-   **Notebooks Panel (Left)**: Create, delete, and switch between your notebooks.
-   **Filters (Top-Right)**: Search your notes, filter by source, and select a date range. The note list updates instantly as you type.
-   **Notes List (Middle-Right)**: Shows a list of your notes from the active notebook, sorted by most recent first. You can right-click on notes here for a context menu with more options.
-   **Detail View (Bottom-Right)**: Displays the full text of the selected note. Use the "Toggle Detail View" button to hide or show this panel.

### Changing the Hotkey

1.  Go to `Settings -> Change Hotkey...`.
2.  Click the "Click to Change" button.
3.  Press your desired new key combination.
4.  Click "Save". The application will restart the hotkey listener with your new shortcut.

## ⚙️ How It Works

Note Harvester runs a background thread that listens for a global hotkey combination. When the hotkey is pressed:
1.  A "capture" task is sent to the main GUI thread.
2.  The hotkey listener is temporarily **paused** to prevent accidental double-triggers or crashes.
3.  The application programmatically simulates a `Ctrl+C` command to copy the highlighted text.
4.  The clipboard content is retrieved, and the original clipboard content is restored.
5.  The captured text, along with its source application title and timestamp, is saved to the active notebook's JSON file.
6.  The hotkey listener is **resumed**, ready for the next capture.

This pause/resume cycle makes the capture process extremely reliable.

## 📄 License

This project is licensed under the MIT License.
