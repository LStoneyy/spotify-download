# spotify-downloaderGUI.py
import os
import sys
import subprocess
import customtkinter as ctk
from tkinter import filedialog, messagebox
import webbrowser

# === Catppuccin Mocha Palette ===
CATPPUCCIN = {
    "base": "#1e1e2e",
    "surface": "#313244",
    "text": "#cdd6f4",
    "blue": "#89b4fa",
    "green": "#a6e3a1",
    "red": "#f38ba8",
    "yellow": "#f9e2af"
}

# === Setup ===
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

class SpotifyDownloaderGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Spotify Playlist Downloader")
        self.geometry("600x400")
        self.configure(fg_color=CATPPUCCIN["base"])

        self.init_ui()

    def init_ui(self):
        # Info label
        info = ctk.CTkLabel(
            self,
            text="🔊 Download your Spotify-Playlist as MP3s without any Login!\n"
                 "1. Export your playlist via Exportify.\n"
                 "2. Upload the CSV file of your playlist here.",
            font=("Segoe UI", 14),
            text_color=CATPPUCCIN["text"],
            justify="left"
        )
        info.pack(pady=(20, 10))

        link = ctk.CTkButton(
            self, text="🔗 Open Exportify",
            command=lambda: webbrowser.open("https://exportify.net/"),
            fg_color=CATPPUCCIN["blue"], text_color="black", hover_color=CATPPUCCIN["green"]
        )
        link.pack(pady=(0, 15))

        # CSV
        self.csv_entry = ctk.CTkEntry(self, placeholder_text="CSV Location", width=400)
        self.csv_entry.pack(pady=5)
        csv_button = ctk.CTkButton(self, text="Add CSV", command=self.browse_csv)
        csv_button.pack(pady=5)

        # Output dir
        self.output_entry = ctk.CTkEntry(self, placeholder_text="Output Folder", width=400)
        self.output_entry.pack(pady=5)
        out_button = ctk.CTkButton(self, text="Select Folder", command=self.browse_output)
        out_button.pack(pady=5)

        # Quality
        self.quality_entry = ctk.CTkEntry(self, placeholder_text="Quality (e.g. 320)", width=100)
        self.quality_entry.insert(0, "320")
        self.quality_entry.pack(pady=10)

        # Start button
        start_btn = ctk.CTkButton(
            self, text="🎵 Start Download",
            command=self.run_downloader,
            fg_color=CATPPUCCIN["green"], text_color="black", hover_color=CATPPUCCIN["yellow"]
        )
        start_btn.pack(pady=(10, 20))

    def browse_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if file_path:
            self.csv_entry.delete(0, "end")
            self.csv_entry.insert(0, file_path)

    def browse_output(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.output_entry.delete(0, "end")
            self.output_entry.insert(0, folder_path)

    def run_downloader(self):
        csv_file = self.csv_entry.get()
        output_dir = self.output_entry.get()
        quality = self.quality_entry.get()

        if not os.path.isfile(csv_file):
            messagebox.showerror("Error", "Please choose a valid CSV.")
            return
        if not os.path.isdir(output_dir):
            messagebox.showerror("Error", "Please choose a valid folder.")
            return
        if quality not in ["128", "192", "256", "320"]:
            messagebox.showerror("Error", "Please choose a valid quality (e.g. 320).")
            return

        os.environ["CSV_FILE"] = csv_file
        os.environ["OUTPUT_DIR"] = output_dir
        os.environ["QUALITY"] = quality

        try:
            subprocess.run([sys.executable, "spotify-to-mp3.py"], check=True)
            messagebox.showinfo("Done", "Download Completed!")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"The script exited:\n{e}")

if __name__ == "__main__":
    app = SpotifyDownloaderGUI()
    app.mainloop()
