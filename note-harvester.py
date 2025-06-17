# --- START OF FILE bn.py ---

import os
import json
import threading
import time
from datetime import datetime, timedelta
import pyperclip
from pynput import keyboard
import pygetwindow as gw
from PIL import Image, ImageDraw, ImageTk
from pystray import Icon as TrayIcon, Menu as TrayMenu, MenuItem as TrayMenuItem
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox, font
import configparser
import logging
import queue
from tkcalendar import DateEntry
import re
import shutil
import tempfile
import subprocess

# Crash Logging Setup
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='note_harvester_crash.log',
    filemode='w'
)

class ConfigManager:
    def __init__(self, filename="config.ini"):
        self.filename = filename
        self.config = configparser.ConfigParser()
        self.default_hotkey = "<ctrl>+<alt>+a"
        self.load_config()

    def load_config(self):
        if not os.path.exists(self.filename): self.create_default_config()
        self.config.read(self.filename)
        return self.config

    def create_default_config(self):
        self.config['Settings'] = {'hotkey': self.default_hotkey}
        with open(self.filename, 'w') as configfile: self.config.write(configfile)

    def get_setting(self, section, key):
        return self.config.get(section, key)

    def set_setting(self, section, key, value):
        if not self.config.has_section(section): self.config.add_section(section)
        self.config.set(section, key, value)
        with open(self.filename, 'w') as configfile: self.config.write(configfile)

class NoteManager:
    def __init__(self, data_folder="Note_Harvester_Data"):
        self.data_path = os.path.join(os.path.expanduser("~"), data_folder)
        os.makedirs(self.data_path, exist_ok=True)

    def get_notebooks(self):
        try:
            files = [f.replace('.json', '') for f in os.listdir(self.data_path) if f.endswith('.json')]
            return sorted(files)
        except FileNotFoundError: return []

    def create_notebook(self, name):
        filepath = os.path.join(self.data_path, f"{name}.json")
        if not os.path.exists(filepath):
            with open(filepath, 'w', encoding='utf-8') as f: json.dump([], f)
            return True
        return False

    def delete_notebook(self, name):
        filepath = os.path.join(self.data_path, f"{name}.json")
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False

    def load_notes(self, notebook_name):
        filepath = os.path.join(self.data_path, f"{notebook_name}.json")
        try:
            with open(filepath, 'r', encoding='utf-8') as f: return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError): return []

    def save_notes(self, notebook_name, notes_data):
        filepath = os.path.join(self.data_path, f"{notebook_name}.json")
        with open(filepath, 'w', encoding='utf-8') as f: json.dump(notes_data, f, ensure_ascii=False, indent=4)

    def add_annotation(self, notebook_name, annotation):
        notes = self.load_notes(notebook_name)
        notes.append(annotation)
        self.save_notes(notebook_name, notes)

class HotkeyService:
    def __init__(self, hotkey_str, callback):
        self.hotkey_str = hotkey_str
        self.callback = callback
        self.listener = None
        self.thread = None

    def start(self):
        if self.is_running(): self.stop()
        try:
            clean_hotkey_str = self.hotkey_str.replace(' ', '')
            self.listener = keyboard.GlobalHotKeys({clean_hotkey_str: self.callback})
            self.thread = threading.Thread(target=self.listener.run, daemon=True)
            self.thread.start()
            print(f"Hotkey listener started with '{clean_hotkey_str}'.")
        except Exception as e:
            logging.error(f"Failed to start hotkey listener: {e}", exc_info=True)
            messagebox.showerror("Hotkey Error", f"Failed to start hotkey listener: {e}\nPlease check the hotkey configuration.")

    def stop(self):
        if self.listener:
            self.listener.stop()
            print("Hotkey listener stopped.")

    def is_running(self):
        return self.thread and self.thread.is_alive()

class SettingsWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Change Hotkey")
        self.geometry("350x150")
        self.transient(parent); self.grab_set(); self.resizable(False, False)
        self.new_hotkey_str = self.parent.config_manager.get_setting('Settings', 'hotkey')
        self.is_recording = False
        self.pressed_keys = set()
        ttk.Label(self, text="Current Hotkey:").pack(pady=(10, 0))
        self.hotkey_label = ttk.Label(self, text=self.new_hotkey_str, font=("Segoe UI", 12, "bold"))
        self.hotkey_label.pack()
        self.record_button = ttk.Button(self, text="Click to Change", command=self.start_recording)
        self.record_button.pack(pady=10)
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Save", command=self.save_and_close).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.LEFT, padx=5)
        self.bind("<KeyPress>", self.on_key_press)
        self.bind("<KeyRelease>", self.on_key_release)

    def start_recording(self):
        self.is_recording = True
        self.record_button.config(text="Press new key combination...")
        self.pressed_keys.clear()

    def on_key_press(self, event):
        if not self.is_recording: return
        key_name = self.get_key_name(event)
        if key_name:
            self.pressed_keys.add(key_name)
            self.hotkey_label.config(text="+".join(sorted(list(self.pressed_keys))))

    def on_key_release(self, event):
        if self.is_recording and self.pressed_keys:
            self.is_recording = False
            self.new_hotkey_str = "+".join(sorted(list(self.pressed_keys)))
            self.hotkey_label.config(text=self.new_hotkey_str)
            self.record_button.config(text="Click to Change")

    def get_key_name(self, event):
        key = event.keysym.lower()
        if key in ('control_l', 'control_r'): return '<ctrl>'
        if key in ('alt_l', 'alt_r'): return '<alt>'
        if key in ('shift_l', 'shift_r'): return '<shift>'
        if len(key) == 1 and key.isalnum(): return key
        return None

    def save_and_close(self):
        self.parent.update_hotkey(self.new_hotkey_str)
        self.destroy()

class DateRangeWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Select Date Range")
        self.transient(parent); self.grab_set()
        ttk.Label(self, text="Start Date:").grid(row=0, column=0, padx=10, pady=5)
        self.start_date_entry = DateEntry(self, date_pattern='y-mm-dd', selectmode='day')
        self.start_date_entry.grid(row=0, column=1, padx=10, pady=5)
        ttk.Label(self, text="End Date:").grid(row=1, column=0, padx=10, pady=5)
        self.end_date_entry = DateEntry(self, date_pattern='y-mm-dd', selectmode='day')
        self.end_date_entry.grid(row=1, column=1, padx=10, pady=5)
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Apply", command=self.apply).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.LEFT, padx=5)

    def apply(self):
        start_date = self.start_date_entry.get_date()
        end_date = self.end_date_entry.get_date()
        self.parent.apply_custom_date_filter(start_date, end_date)
        self.destroy()

class SinglePageViewWindow(tk.Toplevel):
    def __init__(self, parent, notebook_name, notes):
        super().__init__(parent)
        self.parent = parent
        self.title(f"Single Page View - {notebook_name}")
        self.geometry("800x600")
        
        ttk.Label(self, text=f"Notes from '{notebook_name}'", font=("Segoe UI", 14, "bold")).pack(pady=10)
        
        text_frame = ttk.Frame(self)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.text_widget = tk.Text(text_frame, wrap=tk.WORD, padx=10, pady=10)
        
        # *** FIX: Create separate font objects for each tag to be zoomed ***
        self.metadata_font = font.Font(family="Segoe UI", size=9, slant="italic")
        self.content_font = font.Font(family="Segoe UI", size=10)
        self.separator_font = font.Font(family="Segoe UI", size=10) # Font for the separator line
        
        # Configure tags with their respective font objects
        self.text_widget.tag_configure("metadata", font=self.metadata_font, foreground="gray", spacing1=5, spacing3=5)
        self.text_widget.tag_configure("content", font=self.content_font, spacing1=2, spacing3=10)
        # *** FIX: Use a font object and remove the pale foreground color for the separator ***
        self.text_widget.tag_configure("separator", font=self.separator_font, spacing3=10)
        
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.text_widget.yview)
        self.text_widget.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        for note in notes:
            try:
                timestamp = datetime.fromisoformat(note.get("timestamp", "")).strftime('%Y-%m-%d %H:%M:%S')
            except:
                timestamp = "Invalid Date"
            source = note.get("source", "Unknown Source")
            content = note.get("text", "")
            
            self.text_widget.insert(tk.END, f"{timestamp} | {source}\n", "metadata")
            self.text_widget.insert(tk.END, content + "\n", "content")
            self.text_widget.insert(tk.END, "---\n\n", "separator")
        
        self.text_widget.config(state="disabled")
        self._create_zoom_bindings()

    def _create_zoom_bindings(self):
        # Bind directly to the new _zoom method
        self.text_widget.bind("<Control-MouseWheel>", self._zoom)

    def _zoom(self, event):
        # *** FIX: This method now updates all relevant fonts simultaneously ***
        fonts_to_zoom = [self.metadata_font, self.content_font, self.separator_font]
        
        if event.delta > 0:
            for f in fonts_to_zoom:
                f.configure(size=f.cget("size") + 1)
        else:
            # Check one font's size to prevent shrinking too much
            if fonts_to_zoom[0].cget("size") > 6:
                for f in fonts_to_zoom:
                    f.configure(size=f.cget("size") - 1)
        return "break" # Prevents the default scroll behavior

class ExportFormatDialog(simpledialog.Dialog):
    def __init__(self, parent, title=None):
        self.result = None
        super().__init__(parent, title)

    def body(self, master):
        ttk.Label(master, text="Please choose an export format:").pack(pady=10, padx=20)
        return None

    def buttonbox(self):
        box = ttk.Frame(self)
        ttk.Button(box, text="Export as PDF", width=15, command=lambda: self.ok('pdf')).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(box, text="Export as HTML", width=15, command=lambda: self.ok('html')).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(box, text="Cancel", width=10, command=self.cancel).pack(side=tk.LEFT, padx=5, pady=5)
        self.bind("<Escape>", self.cancel)
        box.pack()

    def ok(self, format_choice):
        self.result = format_choice
        super().ok()

class NoteHarvesterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.note_manager = NoteManager()
        self.hotkey_service = None
        self.active_notebook = None
        self.all_notes_cache = {}
        self.detail_view_visible = True
        self.task_queue = queue.Queue()
        self.is_capturing = False
        self.custom_date_filter = None

        self.setup_window()
        self.create_menu()
        self.create_widgets()
        self.create_tray_icon()
        
        self.populate_notebook_list()
        self.restart_hotkey_service()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.poll_queue()

        self.search_var.trace_add("write", lambda *args: self._apply_filters())
        self.case_sensitive_var.trace_add("write", lambda *args: self._apply_filters())
        self.whole_word_var.trace_add("write", lambda *args: self._apply_filters())

    def merge_notes_by_source(self):
        """
        Finds all notes with the same source as the selected note(s)
        and merges them into a single new note.
        """
        selected_items = self.notes_tree.selection()
        if not selected_items:
            messagebox.showinfo("Information", "Please select at least one note to identify the source.", parent=self)
            return

        # Get the source(s) from the selected notes
        all_notes_in_view = self.all_notes_cache.get(self.active_notebook, [])
        target_sources = set(all_notes_in_view[int(i)].get('source') for i in selected_items)
        
        # Confirm with the user
        source_list_str = "', '".join(target_sources)
        if not messagebox.askyesno("Confirm Merge by Source", 
                                   f"Are you sure you want to find ALL notes from source(s) '{source_list_str}' in this notebook and merge them into a new one?\n\nThis will delete all original notes from this source.", 
                                   parent=self):
            return

        # IMPORTANT: Load the full, unfiltered list of notes from the file
        full_note_list = self.note_manager.load_notes(self.active_notebook)

        notes_to_merge = []
        notes_to_keep = []
        for note in full_note_list:
            if note.get('source') in target_sources:
                notes_to_merge.append(note)
            else:
                notes_to_keep.append(note)

        if len(notes_to_merge) < 1:
            messagebox.showinfo("Information", "No notes found for the selected source(s).", parent=self)
            return

        # Sort notes by timestamp to merge them in chronological order
        notes_to_merge.sort(key=lambda x: x.get("timestamp", ""))
        
        # Ask for the new source name, providing a sensible default
        default_new_source = f"Merged from '{source_list_str}'"
        new_source = simpledialog.askstring("New Source", "Enter a source for the merged note:", 
                                            initialvalue=default_new_source, parent=self)
        if not new_source:
            return # User cancelled

        # Create the merged note
        merged_text = "\n\n---\n\n".join(note.get("text", "") for note in notes_to_merge)
        new_note = {"timestamp": datetime.now().isoformat(), "source": new_source, "text": merged_text}
        
        # The new list of notes is the ones we kept plus the new merged one
        final_notes = notes_to_keep + [new_note]
        
        self.note_manager.save_notes(self.active_notebook, final_notes)

        # Clear all filters to ensure the new merged note is visible
        self.search_var.set("")
        self.source_filter_var.set("All Sources")
        self.custom_date_filter = None
        self.date_filter_btn.config(text="All Time")
        
        # Repopulate the treeview
        self.populate_notes_treeview()
        
        # Safely select the new note (it will be the first one after re-populating)
        all_tree_items = self.notes_tree.get_children()
        if all_tree_items:
            new_note_iid = all_tree_items[0]
            self.notes_tree.selection_set(new_note_iid)
            self.notes_tree.focus(new_note_iid)
            self.notes_tree.see(new_note_iid)
            self.on_note_select()
            
        self.flash_status(f"{len(notes_to_merge)} notes merged successfully!")

    def _escape_latex(self, text):
        """Escapes special LaTeX characters in a given string."""
        # Bu karakterler LaTeX'te özel anlamlara sahiptir.
        # Onları bir ters eğik çizgi ile "kaçarak" etkisiz hale getiriyoruz.
        # Ters eğik çizginin kendisi en karmaşık olanıdır ve \textbackslash{} ile değiştirilmelidir.
        conv = {
            '&': r'\&',
            '%': r'\%',
            '$': r'\$',
            '#': r'\#',
            '_': r'\_',
            '{': r'\{',
            '}': r'\}',
            '~': r'\textasciitilde{}',
            '^': r'\textasciicircum{}',
            '\\': r'\textbackslash{}',
        }
        # Regex kullanarak bu karakterleri bulup değiştiriyoruz.
        # Bu, basit replace() çağrılarından daha güvenlidir.
        regex = re.compile('|'.join(re.escape(key) for key in sorted(conv.keys(), key=len, reverse=True)))
        return regex.sub(lambda match: conv[match.group()], text)

    def setup_window(self):
        self.title("Note Harvester v2.5 (Final)")
        self.geometry("1100x700")
        self.iconphoto(True, self.generate_tk_icon())

    def create_menu(self):
        menu_bar = tk.Menu(self)
        self.config(menu=menu_bar)
        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="View as Single Page (P)", command=self.show_as_single_page)
        file_menu.add_command(label="Export to PDF/HTML", command=self.export_to_pandoc)
        file_menu.add_command(label="Minimize to Tray", command=self.withdraw)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit_app)
        self.show_date_var = tk.BooleanVar(value=True)
        self.show_source_var = tk.BooleanVar(value=True)
        view_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="View", menu=view_menu)
        view_menu.add_checkbutton(label="Show Date Column", variable=self.show_date_var, command=self._update_visible_columns)
        view_menu.add_checkbutton(label="Show Source Column", variable=self.show_source_var, command=self._update_visible_columns)
        settings_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Change Hotkey...", command=self.open_settings)

    def create_widgets(self):
        main_pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        left_frame = ttk.Frame(main_pane, width=250)
        main_pane.add(left_frame, weight=1)
        ttk.Label(left_frame, text="Notebooks", font=("Segoe UI", 12, "bold")).pack(pady=5, anchor="w")
        self.notebook_listbox = tk.Listbox(left_frame, exportselection=False, font=("Segoe UI", 10))
        self.notebook_listbox.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        self.notebook_listbox.bind("<<ListboxSelect>>", self.on_notebook_select)
        self.notebook_listbox.bind("<Delete>", lambda e: self.delete_selected_notebook())
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="New", command=self.create_new_notebook).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,2))
        ttk.Button(btn_frame, text="Delete", command=self.delete_selected_notebook).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(2,0))
        self.right_pane = ttk.PanedWindow(main_pane, orient=tk.VERTICAL)
        main_pane.add(self.right_pane, weight=4)
        notes_frame = ttk.Frame(self.right_pane)
        self.right_pane.add(notes_frame, weight=3)
        filter_frame = ttk.LabelFrame(notes_frame, text="Filters")
        filter_frame.pack(fill=tk.X, pady=5, padx=5)
        ttk.Label(filter_frame, text="Search Text:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(filter_frame, textvariable=self.search_var)
        self.search_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.case_sensitive_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(filter_frame, text="Case Sensitive", variable=self.case_sensitive_var).grid(row=0, column=2, padx=5, pady=5)
        self.whole_word_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(filter_frame, text="Whole Word", variable=self.whole_word_var).grid(row=0, column=3, padx=5, pady=5)
        ttk.Label(filter_frame, text="Source:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.source_filter_var = tk.StringVar()
        self.source_filter_combo = ttk.Combobox(filter_frame, textvariable=self.source_filter_var, state="readonly")
        self.source_filter_combo.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.source_filter_combo.bind("<<ComboboxSelected>>", lambda e: self._apply_filters())
        ttk.Label(filter_frame, text="Date Range:").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.date_filter_btn = ttk.Button(filter_frame, text="All Time", command=self.open_date_range_window)
        self.date_filter_btn.grid(row=1, column=3, padx=5, pady=5, sticky="ew")
        filter_frame.columnconfigure(1, weight=1); filter_frame.columnconfigure(3, weight=1)
        tree_frame = ttk.Frame(notes_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5)
        cols = ("Date", "Source", "Summary")
        self.notes_tree = ttk.Treeview(tree_frame, columns=cols, show="headings", selectmode="extended")
        self.notes_tree.bind("<<TreeviewSelect>>", self.on_note_select)
        self.notes_tree.bind("<Button-3>", self._show_context_menu)
        self.notes_tree.bind("<B1-Motion>", self._handle_drag_select)
        self.notes_tree.bind("<Delete>", lambda e: self.delete_selected_notes_from_context())
        for col in cols: self.notes_tree.heading(col, text=col)
        self.notes_tree.column("Date", width=150, stretch=False); self.notes_tree.column("Source", width=200, stretch=False); self.notes_tree.column("Summary", width=400)
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.notes_tree.yview)
        self.notes_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.notes_tree.xview)
        self.notes_tree.configure(xscrollcommand=h_scrollbar.set)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.notes_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.detail_frame = ttk.Frame(self.right_pane)
        self.right_pane.add(self.detail_frame, weight=2)
        ttk.Label(self.detail_frame, text="Selected Note Detail", font=("Segoe UI", 12, "bold")).pack(pady=5, anchor="w", padx=5)
        self.note_detail_text = tk.Text(self.detail_frame, wrap=tk.WORD, padx=5, pady=5)
        self.detail_font = font.Font(family="Segoe UI", size=10)
        self.note_detail_text.configure(font=self.detail_font)
        self.note_detail_text.config(state="disabled")
        self._create_zoom_bindings(self.note_detail_text, self.detail_font)
        self.note_detail_text.pack(fill=tk.BOTH, expand=True, padx=5)
        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_bar = ttk.Label(bottom_frame, text="Ready", relief=tk.SUNKEN, anchor=tk.W, padding=5)
        self.status_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(bottom_frame, text="Merge Selected", command=self.merge_selected_notes).pack(side=tk.RIGHT, padx=(0,5), pady=5)
        ttk.Button(bottom_frame, text="Toggle Detail View", command=self.toggle_detail_view).pack(side=tk.RIGHT, padx=5, pady=5)
        self.after(20, lambda: self.right_pane.sashpos(0, 400))
        
        self.bind("<p>", self.on_p_key)

    def on_p_key(self, event):
        if self.focus_get() != self.search_entry:
            self.show_as_single_page()

    def populate_notebook_list(self, select_first=True):
        self.notebook_listbox.delete(0, tk.END)
        notebooks = self.note_manager.get_notebooks()
        for nb in notebooks:
            self.notebook_listbox.insert(tk.END, nb)
        if notebooks and select_first:
            self.notebook_listbox.selection_set(0)
            self.on_notebook_select()

    def poll_queue(self):
        try:
            task = self.task_queue.get_nowait()
            if task == "CAPTURE_NOTE":
                self.execute_annotation_capture()
        except queue.Empty:
            pass
        finally:
            self.after(100, self.poll_queue)

    def execute_annotation_capture(self):
        if self.is_capturing: return
        self.is_capturing = True
        self.hotkey_service.stop()
        try:
            if not self.active_notebook:
                self.flash_status("Error: Please select a notebook in the UI.")
                return
            source = gw.getActiveWindow().title if gw.getActiveWindow() else "Unknown Source"
            original_clipboard = pyperclip.paste()
            pyperclip.copy('')
            controller = keyboard.Controller()
            with controller.pressed(keyboard.Key.ctrl): controller.press('c'); controller.release('c')
            time.sleep(0.1)
            selected_text = pyperclip.paste()
            pyperclip.copy(original_clipboard)
            if selected_text and not selected_text.isspace():
                annotation = {"timestamp": datetime.now().isoformat(), "source": source, "text": selected_text}
                self.note_manager.add_annotation(self.active_notebook, annotation)
                self.flash_status(f"Note saved to '{self.active_notebook}'!")
                if self.state() == 'normal':
                    self._update_source_filter()
                    self.populate_notes_treeview()
            else:
                self.flash_status("Capture failed: No text selected.")
        except Exception as e:
            logging.error(f"Error during annotation execution: {e}", exc_info=True)
            self.flash_status("An error occurred during capture.")
        finally:
            self.hotkey_service.start()
            self.is_capturing = False

    def restart_hotkey_service(self):
        if self.hotkey_service: self.hotkey_service.stop()
        hotkey_str = self.config_manager.get_setting('Settings', 'hotkey')
        callback = lambda: self.task_queue.put("CAPTURE_NOTE")
        self.hotkey_service = HotkeyService(hotkey_str, callback)
        self.hotkey_service.start()

    def populate_notes_treeview(self):
        if not self.active_notebook: return
        for i in self.notes_tree.get_children(): self.notes_tree.delete(i)
        self.note_detail_text.config(state="normal"); self.note_detail_text.delete("1.0", tk.END); self.note_detail_text.config(state="disabled")
        notes = self.note_manager.load_notes(self.active_notebook)
        filter_text = self.search_var.get()
        filter_source = self.source_filter_var.get()
        if filter_text:
            flags = 0 if self.case_sensitive_var.get() else re.IGNORECASE
            if self.whole_word_var.get():
                pattern = r'\b' + re.escape(filter_text) + r'\b'
            else:
                pattern = re.escape(filter_text)
            regex = re.compile(pattern, flags)
            notes = [n for n in notes if regex.search(n.get('text', '')) or regex.search(n.get('source', ''))]
        if filter_source and filter_source != "All Sources": notes = [n for n in notes if n.get('source') == filter_source]
        if self.custom_date_filter:
            start, end = self.custom_date_filter
            end_of_day = end + timedelta(days=1)
            notes = [n for n in notes if start <= datetime.fromisoformat(n.get('timestamp')).date() < end_of_day]
        notes.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        self.all_notes_cache[self.active_notebook] = notes
        style = ttk.Style()
        style.configure("Treeview", rowheight=20)
        for i, note in enumerate(notes):
            text = note.get("text", "")
            source = note.get("source", "Unknown")
            try: timestamp = datetime.fromisoformat(note.get("timestamp", "")).strftime('%Y-%m-%d %H:%M:%S')
            except: timestamp = "Invalid Date"
            summary = (text[:75] + '...' if len(text) > 75 else text)
            self.notes_tree.insert("", tk.END, iid=i, values=(timestamp, source, summary.replace("\n", " ")))

    def _handle_drag_select(self, event):
        item = self.notes_tree.identify_row(event.y)
        if item: self.notes_tree.selection_add(item)

    def _show_context_menu(self, event):
        selection = self.notes_tree.selection()
        if not selection:
            item = self.notes_tree.identify_row(event.y)
            if not item: return
            self.notes_tree.selection_set(item)
            selection = self.notes_tree.selection()
            
        context_menu = tk.Menu(self, tearoff=0)
        
        if len(selection) == 1:
            context_menu.add_command(label="Copy Full Text", command=lambda: self._copy_from_context('text'))
            context_menu.add_command(label="Copy Source", command=lambda: self._copy_from_context('source'))
            context_menu.add_command(label="Copy Timestamp", command=lambda: self._copy_from_context('timestamp'))
        else:
            context_menu.add_command(label=f"Copy {len(selection)} Full Texts", command=lambda: self._copy_from_context('text', multi=True))
        
        context_menu.add_separator()
        
        if len(selection) > 1:
            context_menu.add_command(label="Merge Selected", command=self.merge_selected_notes)
        
        # --- START OF CHANGE ---
        # Add the new "Merge by Source" option. It's available even if only one note is selected.
        if selection:
            context_menu.add_command(label="Merge All by Source", command=self.merge_notes_by_source)
        # --- END OF CHANGE ---
            
        context_menu.add_command(label="Delete Selected", command=self.delete_selected_notes_from_context)
        context_menu.tk_popup(event.x_root, event.y_root)

    def _copy_from_context(self, key, multi=False):
        selection = self.notes_tree.selection()
        if not selection: return
        if not multi:
            note = self.all_notes_cache.get(self.active_notebook, [])[int(selection[0])]
            pyperclip.copy(note.get(key, ''))
            self.flash_status(f"{key.capitalize()} copied to clipboard!")
        else:
            all_notes = self.all_notes_cache.get(self.active_notebook, [])
            texts = [all_notes[int(i)].get(key, '') for i in selection]
            pyperclip.copy("\n\n---\n\n".join(texts))
            self.flash_status(f"{len(selection)} texts copied to clipboard!")

    def _create_zoom_bindings(self, widget, font_obj):
        widget.bind("<Control-MouseWheel>", lambda event: self._zoom(event, widget, font_obj))

    def _zoom(self, event, widget, font_obj):
        if event.delta > 0: font_obj.configure(size=font_obj.cget("size") + 1)
        else:
            if font_obj.cget("size") > 6: font_obj.configure(size=font_obj.cget("size") - 1)
        return "break"

    def open_date_range_window(self):
        DateRangeWindow(self)

    def apply_custom_date_filter(self, start_date, end_date):
        self.custom_date_filter = (start_date, end_date)
        self.date_filter_btn.config(text=f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}")
        self._apply_filters()

    def _apply_filters(self, *args):
        self.populate_notes_treeview()

    def on_notebook_select(self, event=None):
        selection = self.notebook_listbox.curselection()
        if not selection: return
        self.active_notebook = self.notebook_listbox.get(selection[0])
        self.status_bar.config(text=f"Active Notebook: {self.active_notebook}")
        self._update_source_filter()
        self._apply_filters()

    def on_note_select(self, event=None):
        if not self.detail_view_visible: return
        item_id = self.notes_tree.focus()
        if not item_id: return
        note = self.all_notes_cache.get(self.active_notebook, [])[int(item_id)]
        self.note_detail_text.config(state="normal")
        self.note_detail_text.delete("1.0", tk.END)
        self.note_detail_text.insert("1.0", note.get("text", ""))
        self.note_detail_text.config(state="disabled")

    def flash_status(self, message, duration=3000):
        self.status_bar.config(text=message)
        self.after(duration, lambda: self.status_bar.config(text=f"Active Notebook: {self.active_notebook}"))

    def open_settings(self):
        SettingsWindow(self)

    def update_hotkey(self, new_hotkey_str):
        self.config_manager.set_setting('Settings', 'hotkey', new_hotkey_str)
        self.restart_hotkey_service()
        messagebox.showinfo("Success", f"Hotkey updated to '{new_hotkey_str}'.")

    def create_tray_icon(self):
        image = self.generate_tray_icon_image()
        menu = TrayMenu(TrayMenuItem("Show", self.show_window, default=True), TrayMenuItem("Exit", self.quit_app))
        self.tray_icon = TrayIcon("NoteHarvester", image, "Note Harvester", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def on_closing(self):
        if messagebox.askyesno("Exit", "Do you want to exit the application completely?\n\n(Select 'No' to minimize to the system tray)"):
            self.quit_app()
        else:
            self.withdraw()

    def quit_app(self):
        if self.hotkey_service: self.hotkey_service.stop()
        if self.tray_icon: self.tray_icon.stop()
        self.destroy()

    def show_window(self):
        self.deiconify(); self.lift(); self.focus_force()

    def generate_tk_icon(self):
        image = Image.new('RGB', (32, 32), '#333333')
        dc = ImageDraw.Draw(image)
        dc.text((8, 4), "H", fill='#FFFFFF', font_size=24)
        return ImageTk.PhotoImage(image)

    def generate_tray_icon_image(self):
        image = Image.new('RGB', (64, 64), '#333333')
        dc = ImageDraw.Draw(image)
        dc.text((18, 18), "H", fill='#FFFFFF', font_size=32)
        return image
    
    def create_new_notebook(self):
        name = simpledialog.askstring("New Notebook", "Enter the name for the new notebook:", parent=self)
        if name and name.strip():
            if self.note_manager.create_notebook(name.strip()):
                self.populate_notebook_list(select_first=False)
                for i, item in enumerate(self.notebook_listbox.get(0, tk.END)):
                    if item == name.strip(): self.notebook_listbox.selection_set(i); self.on_notebook_select(); break
            else: messagebox.showwarning("Error", f"A notebook named '{name}' already exists.", parent=self)

    def delete_selected_notebook(self):
        selection = self.notebook_listbox.curselection()
        if not selection: messagebox.showinfo("Information", "Please select a notebook to delete.", parent=self); return
        name = self.notebook_listbox.get(selection[0])
        if messagebox.askyesno("Confirm Deletion", f"Are you sure you want to permanently delete the notebook '{name}' and all its contents?", parent=self):
            self.note_manager.delete_notebook(name)
            self.populate_notebook_list()

    def merge_selected_notes(self):
        selected_items = self.notes_tree.selection()
        if len(selected_items) < 2:
            messagebox.showinfo("Information", "Please select at least two notes to merge.", parent=self)
            return
        if not messagebox.askyesno("Confirm Merge", f"Are you sure you want to merge {len(selected_items)} notes into a new one and delete the originals?", parent=self):
            return
        new_source = simpledialog.askstring("New Source", "Enter a source for the merged note:", initialvalue="Merged Note", parent=self)
        if not new_source:
            return
            
        # Get all notes currently displayed in the treeview
        all_notes = self.all_notes_cache.get(self.active_notebook, [])
        
        # Get the actual note data for the selected items
        selected_notes = [all_notes[int(i)] for i in selected_items]
        
        # Combine the text from the selected notes
        merged_text = "\n\n---\n\n".join(note.get("text", "") for note in selected_notes)
        new_note = {"timestamp": datetime.now().isoformat(), "source": new_source, "text": merged_text}
        
        # Get the full list of notes from the file to ensure we don't lose anything
        # This is safer than relying on the potentially filtered cache
        full_note_list = self.note_manager.load_notes(self.active_notebook)
        
        # Create a set of the texts of the notes to be deleted for accurate removal
        texts_to_delete = {note['text'] for note in selected_notes}
        timestamps_to_delete = {note['timestamp'] for note in selected_notes}

        # Filter out the original notes from the full list
        remaining_notes = [
            note for note in full_note_list 
            if not (note.get('text') in texts_to_delete and note.get('timestamp') in timestamps_to_delete)
        ]
        
        remaining_notes.append(new_note)
        
        self.note_manager.save_notes(self.active_notebook, remaining_notes)
        
        # --- START OF FIX ---
        # Clear all active filters to ensure the new merged note is visible.
        # This prevents the "Item not found" error when filters would hide the new note.
        self.search_var.set("")
        self.source_filter_var.set("All Sources")
        self.custom_date_filter = None
        self.date_filter_btn.config(text="All Time")
        
        # Repopulate the treeview with all filters cleared.
        self.populate_notes_treeview()
        
        # Safely select the new note. After clearing filters and re-sorting,
        # the newest note (the one we just created) will be the first item.
        # We add a check to ensure the tree is not empty before selecting.
        all_tree_items = self.notes_tree.get_children()
        if all_tree_items:
            new_note_iid = all_tree_items[0]  # The most recent note is at the top
            self.notes_tree.selection_set(new_note_iid)
            self.notes_tree.focus(new_note_iid)
            self.notes_tree.see(new_note_iid) # Ensure the selected item is visible
            self.on_note_select()
        # --- END OF FIX ---
            
        self.flash_status("Notes merged successfully!")

    def delete_selected_notes_from_context(self):
        if not self.notes_tree.selection(): messagebox.showinfo("Information", "No notes selected to delete.", parent=self); return
        if messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete {len(self.notes_tree.selection())} note(s)?", parent=self):
            all_notes = self.all_notes_cache.get(self.active_notebook, [])
            indices_to_delete = {int(i) for i in self.notes_tree.selection()}
            remaining_notes = [note for i, note in enumerate(all_notes) if i not in indices_to_delete]
            self.note_manager.save_notes(self.active_notebook, remaining_notes)
            self.populate_notes_treeview()
            self.flash_status("Note(s) deleted.")

    def _update_visible_columns(self):
        visible_cols = [col for var, col in [(self.show_date_var, "Date"), (self.show_source_var, "Source")] if var.get()]
        visible_cols.append("Summary")
        self.notes_tree['displaycolumns'] = visible_cols

    def toggle_detail_view(self):
        if self.detail_view_visible:
            self.right_pane.forget(self.detail_frame)
            self.detail_view_visible = False
        else:
            self.right_pane.add(self.detail_frame, weight=2)
            self.detail_view_visible = True

    def show_as_single_page(self):
        if not self.active_notebook: messagebox.showinfo("Information", "Please select a notebook first.", parent=self); return
        notes = self.all_notes_cache.get(self.active_notebook, [])
        if not notes: messagebox.showinfo("Information", "This notebook is empty.", parent=self); return
        SinglePageViewWindow(self, self.active_notebook, notes)

    def _update_source_filter(self):
        if not self.active_notebook: return
        notes = self.note_manager.load_notes(self.active_notebook)
        sources = sorted(list(set(n.get('source', 'Unknown') for n in notes)))
        self.source_filter_combo['values'] = ["All Sources"] + sources
        self.source_filter_var.set("All Sources")

    def generate_markdown(self, notes):
        # --- START OF FIX ---
        # \makefullwidthline komutunu tanımlıyoruz. Bu komut, sayfanın tam
        # genişliğinde bir çizgi çeker. \noindent ile girintiyi kaldırır,
        # \rule ile çizginin genişliğini ve kalınlığını belirleriz.
        # \linewidth, metin bloğunun genişliğidir.
        yaml_header = """---
geometry: "a4paper, margin=2.5cm"
header-includes:
  - \\usepackage{ragged2e}
  - \\RaggedRight
  - \\setlength{\\parindent}{0pt}
  - \\usepackage{parskip}
  - \\newcommand{\\fullwidthline}{\\noindent\\rule{\\linewidth}{0.4pt}}
---
"""
        # --- END OF FIX ---

        md_lines = [yaml_header]
        for note in notes:
            timestamp = note.get("timestamp", "Unknown")
            try:
                timestamp = datetime.fromisoformat(timestamp).strftime('%Y-%m-%d %H:%M:%S')
            except:
                pass
            
            source = self._escape_latex(note.get("source", "Unknown"))
            text = self._escape_latex(note.get("text", ""))

            # --- START OF FIX ---
            # Standart '---' yerine, tanımladığımız özel LaTeX komutunu kullanıyoruz.
            # İki satır boşluk bırakarak okunabilirliği artırıyoruz.
            md_lines.append(f"### {timestamp} | {source}\n\n{text}\n\n\\fullwidthline\n")
            # --- END OF FIX ---
            
        return "\n".join(md_lines)

    def export_to_pandoc(self):
        if not self.active_notebook:
            messagebox.showinfo("Information", "Please select a notebook first.", parent=self)
            return
        notes = self.all_notes_cache.get(self.active_notebook, [])
        if not notes:
            messagebox.showinfo("Information", "This notebook is empty.", parent=self)
            return
        if not shutil.which('pandoc'):
            messagebox.showerror("Error", "Pandoc is not installed or not in PATH. Please install Pandoc to use this feature.")
            return
        
        dialog = ExportFormatDialog(self, title="Choose Export Format")
        format_choice = dialog.result

        if not format_choice:
            return
        
        md_content = self.generate_markdown(notes)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            safe_notebook_name = re.sub(r'[\\/*?:"<>|]', "", self.active_notebook)
            base_filename = f"{safe_notebook_name}_{datetime.now().strftime('%Y%m%d')}"
            
            from tkinter import filedialog
            output_path = filedialog.asksaveasfilename(
                initialdir=os.path.expanduser("~"),
                initialfile=f"{base_filename}.{format_choice}",
                defaultextension=f".{format_choice}",
                filetypes=[(f"{format_choice.upper()} files", f"*.{format_choice}"), ("All files", "*.*")]
            )

            if not output_path:
                return

            md_path = os.path.join(tmpdir, "export.md")
            with open(md_path, 'w', encoding='utf-8') as tmp_md:
                tmp_md.write(md_content)

            try:
                command = ['pandoc', md_path, '-o', output_path]
                if format_choice == 'pdf':
                    command.extend(['--pdf-engine=pdflatex'])
                
                subprocess.run(command, check=True)
                
                messagebox.showinfo("Success", f"Successfully exported to:\n{output_path}", parent=self)
                
                if os.name == 'nt':
                    os.startfile(output_path)
                else:
                    subprocess.run(['xdg-open', output_path])

            except subprocess.CalledProcessError as e:
                error_message = f"Pandoc conversion failed: {e}"
                if "pdflatex not found" in str(e):
                    error_message += "\n\nIt seems a LaTeX distribution (like MiKTeX or TeX Live) is not installed. It's required for PDF export."
                messagebox.showerror("Error", error_message, parent=self)
            except Exception as e:
                messagebox.showerror("Error", f"An unexpected error occurred during export: {e}", parent=self)


if __name__ == "__main__":
    try:
        app = NoteHarvesterApp()
        app.mainloop()
    except Exception as e:
        logging.critical("Application encountered a fatal error!", exc_info=True)
        messagebox.showerror("Fatal Error", f"A critical error occurred: {e}\n\nDetails have been saved to 'note_harvester_crash.log'.")