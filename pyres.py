import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
import subprocess
import threading
import os
import platform
import shlex


class FFmpegConverter:
    def __init__(self, master):
        self.master = master
        self.master.title("PyRes")
        self.master.geometry("800x600")

        self.file_list = []

        self.create_widgets()

    def create_widgets(self):
        self.drop_frame = ttk.LabelFrame(self.master, text="Drag & Drop Files or Use 'Open Files'")
        self.drop_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.file_listbox = tk.Listbox(self.drop_frame, selectmode=tk.EXTENDED)
        self.file_listbox.pack(fill="both", expand=True, padx=5, pady=5)

        self.file_listbox.drop_target_register(DND_FILES)
        self.file_listbox.dnd_bind('<<Drop>>', self.on_drop)

        self.controls_frame = ttk.Frame(self.master)
        self.controls_frame.pack(fill="x", padx=10, pady=5)

        self.open_button = ttk.Button(self.controls_frame, text="Open Files", command=self.open_files)
        self.open_button.pack(side="left", padx=5)

        self.codec_label = ttk.Label(self.controls_frame, text="ProRes Profile:")
        self.codec_label.pack(side="left")

        self.codec_choice = ttk.Combobox(self.controls_frame, values=["0 - Proxy", "1 - LT", "2 - Standard", "3 - HQ"], state="readonly")
        self.codec_choice.current(2)  # Default to Standard
        self.codec_choice.pack(side="left", padx=5)

        self.convert_button = ttk.Button(self.controls_frame, text="Convert", command=self.start_conversion)
        self.convert_button.pack(side="right", padx=5)

        self.progress = ttk.Progressbar(self.master, orient="horizontal", mode="determinate")
        self.progress.pack(fill="x", padx=10, pady=5)

        self.output_text = tk.Text(self.master, height=15)
        self.output_text.pack(fill="both", expand=True, padx=10, pady=5)
        self.output_text.configure(state="disabled")

    def log(self, message):
        self.output_text.configure(state="normal")
        self.output_text.insert(tk.END, message + "\n")
        self.output_text.see(tk.END)
        self.output_text.configure(state="disabled")

    def on_drop(self, event):
        self.log(f"Raw drop data: {event.data!r}")
        paths = self.parse_dropped_files(event.data)
        for path in paths:
            if os.path.isfile(path):
                self.file_listbox.insert(tk.END, path)
            else:
                self.log(f"Ignored non-file: {path}")

    def parse_dropped_files(self, dropped_data):
        if not dropped_data:
            return []

        if platform.system() == "Windows":
            # This will handle paths with spaces and braces
            cleaned = []
            buffer = ""
            inside_brace = False
            for token in dropped_data.strip().split():
                if token.startswith("{"):
                    buffer = token
                    inside_brace = True
                elif inside_brace:
                    buffer += f" {token}"
                    if token.endswith("}"):
                        inside_brace = False
                        cleaned.append(os.path.abspath(buffer[1:-1]))
                else:
                    cleaned.append(os.path.abspath(token.strip('{}')))
            return cleaned
        else:
            return [os.path.abspath(path) for path in shlex.split(dropped_data)]

    def open_files(self):
        files = filedialog.askopenfilenames(title="Select Video Files")
        for file in files:
            self.file_listbox.insert(tk.END, file)

    def start_conversion(self):
        self.file_list = list(self.file_listbox.get(0, tk.END))
        if not self.file_list:
            self.log("No files to convert.")
            return

        profile_index = self.codec_choice.current()

        self.progress["maximum"] = len(self.file_list)
        self.progress["value"] = 0

        self.log("Starting conversion...")

        threading.Thread(target=self.convert_all_files, args=(profile_index,), daemon=True).start()

    def convert_all_files(self, profile):
        for i, filepath in enumerate(self.file_list):
            self.convert_file(filepath, profile)
            self.progress["value"] = i + 1

        self.log("Conversion complete.")

    def convert_file(self, filepath, profile):
        dirname, filename = os.path.split(filepath)
        name, _ = os.path.splitext(filename)
        output_file = os.path.join(dirname, f"{name}_prores.mov")

        command = [
            "ffmpeg",
            "-i", filepath,
            "-c:v", "prores_ks",
            "-profile:v", str(profile),
            "-pix_fmt", "yuv422p10le",
            "-c:a", "copy",
            output_file
        ]

        self.log(f"\nConverting: {filepath}")
        self.log("Command: " + " ".join(shlex.quote(arg) for arg in command))

        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )

            for line in process.stdout:
                self.log(line.strip())

            return_code = process.wait()
            if return_code != 0:
                raise subprocess.CalledProcessError(return_code, command)

            self.log(f"Finished: {output_file}")
        except FileNotFoundError:
            self.log("FFmpeg executable not found. Please ensure ffmpeg is installed and accessible in your system PATH.")
            messagebox.showerror("Error", "FFmpeg executable not found. Please ensure ffmpeg is installed and accessible in your system PATH.")
        except subprocess.CalledProcessError as e:
            self.log(f"Error during conversion of {filepath}: Return code {e.returncode}")
            messagebox.showerror("Conversion Error", f"Error occurred while converting {filepath}. Check the log for details.")


if __name__ == '__main__':
    app = TkinterDnD.Tk()
    FFmpegConverter(app)
    app.mainloop()