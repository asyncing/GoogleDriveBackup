import customtkinter as ctk
from customtkinter import filedialog
import os
import datetime
import threading
import subprocess
import winreg
import re
import time

save_destination = os.path.join(os.path.expanduser("~"), "Desktop")
selected_folders = []
CONFIG_FILE = "backup_folders.txt"
winrar_exe_path = None
is_running = False
cancel_requested = False
current_backup_path = ""

ctk.set_appearance_mode("dark")

app = ctk.CTk()
app.title("WinRAR Backup Utility")
app.geometry("620x720")
app.minsize(550, 600)
app.resizable(True, True)
app.configure(fg_color="#0d0d12")
app.attributes("-alpha", 0.0)

main_font = ("Segoe UI", 14)
header_font = ("Segoe UI", 26, "bold")
button_font = ("Segoe UI", 13, "bold")
mono_font = ("Consolas", 13)

header_label = ctk.CTkLabel(app, text="WinRAR Backup", font=header_font, text_color="#a855f7")
header_label.pack(pady=(30, 20))

settings_frame = ctk.CTkFrame(app, fg_color="#181822", corner_radius=15, border_width=1, border_color="#272735")
settings_frame.pack(fill="x", padx=30, pady=(0, 15))

dest_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
dest_frame.pack(fill="x", padx=20, pady=(20, 10))

dest_label = ctk.CTkLabel(dest_frame, text=f"Saving to: {save_destination}", font=main_font, text_color="#d4d4d8",
                          anchor="w")
dest_label.pack(side="left", fill="x", expand=True, padx=(0, 10))

change_dest_btn = ctk.CTkButton(dest_frame, text="Browse", width=80, font=button_font,
                                fg_color="#272735", hover_color="#3f3f5a", text_color="#e4e4e7", corner_radius=8)
change_dest_btn.pack(side="right")

delete_old_switch = ctk.CTkSwitch(settings_frame, text="Delete old backups after running", font=main_font,
                                  text_color="#d4d4d8", progress_color="#a855f7", button_color="#ffffff",
                                  button_hover_color="#e4e4e7")
delete_old_switch.pack(anchor="w", padx=20, pady=(5, 20))

folders_frame = ctk.CTkFrame(app, fg_color="#181822", corner_radius=15, border_width=1, border_color="#272735")
folders_frame.pack(fill="both", expand=True, padx=30, pady=10)

title_label = ctk.CTkLabel(folders_frame, text="Selected Folders", font=("Segoe UI", 16, "bold"), text_color="#e4e4e7")
title_label.pack(anchor="w", padx=20, pady=(20, 5))

textbox = ctk.CTkTextbox(folders_frame, font=mono_font, fg_color="#111116",
                         text_color="#a1a1aa", border_width=1, border_color="#272735", corner_radius=10)
textbox.pack(fill="both", expand=True, padx=20, pady=10)

button_frame = ctk.CTkFrame(folders_frame, fg_color="transparent")
button_frame.pack(fill="x", padx=20, pady=(5, 20))

add_btn = ctk.CTkButton(button_frame, text="+ Add Folder", font=button_font,
                        fg_color="#10b981", hover_color="#059669", text_color="#ffffff", corner_radius=8)
add_btn.pack(side="left")

clear_btn = ctk.CTkButton(button_frame, text="Clear List", font=button_font,
                          fg_color="#ef4444", hover_color="#dc2626", text_color="#ffffff", corner_radius=8)
clear_btn.pack(side="right")

action_frame = ctk.CTkFrame(app, fg_color="transparent")
action_frame.pack(fill="x", padx=30, pady=(15, 30))

progress_bar = ctk.CTkProgressBar(action_frame, height=14, fg_color="#272735", progress_color="#a855f7",
                                  corner_radius=7)
progress_bar.pack(fill="x")
progress_bar.set(0)

percentage_label = ctk.CTkLabel(action_frame, text="0%", font=("Segoe UI", 14, "bold"), text_color="#a855f7")
percentage_label.pack(pady=(5, 15))

btn_container = ctk.CTkFrame(action_frame, fg_color="transparent")
btn_container.pack(fill="x")

run_btn = ctk.CTkButton(btn_container, text="START BACKUP", font=("Segoe UI", 16, "bold"),
                        fg_color="#9333ea", hover_color="#7e22ce", text_color="#ffffff", height=45, corner_radius=12)
run_btn.pack(side="left", fill="x", expand=True, padx=(0, 10))

cancel_btn = ctk.CTkButton(btn_container, text="CANCEL", font=("Segoe UI", 16, "bold"),
                           fg_color="#ef4444", hover_color="#dc2626", text_color="#ffffff", height=45, corner_radius=12,
                           width=100, state="disabled")
cancel_btn.pack(side="right")

status_label = ctk.CTkLabel(action_frame, text="Ready.", font=main_font, text_color="#71717a")
status_label.pack(pady=(15, 0))


def fade_in_window(alpha=0.0):
    alpha += 0.05
    if alpha <= 1.0:
        app.attributes("-alpha", alpha)
        app.after(15, lambda: fade_in_window(alpha))


def load_saved_folders():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            for line in f:
                folder = line.strip()
                if os.path.exists(folder) and folder not in selected_folders:
                    selected_folders.append(folder)
                    textbox.insert("end", folder + "\n")


def find_winrar():
    try:
        reg_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\WinRAR.exe"
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
        winrar_exe, _ = winreg.QueryValueEx(key, "")
        winreg.CloseKey(key)

        winrar_dir = os.path.dirname(winrar_exe)
        rar_path = os.path.join(winrar_dir, "Rar.exe")

        if os.path.exists(rar_path):
            return rar_path
    except Exception:
        pass

    common_paths = [
        r"C:\Program Files\WinRAR\Rar.exe",
        r"C:\Program Files (x86)\WinRAR\Rar.exe"
    ]
    for path in common_paths:
        if os.path.exists(path):
            return path

    return None


def change_destination():
    global save_destination
    folder_path = filedialog.askdirectory(title="Select Save Location")
    if folder_path:
        save_destination = folder_path
        dest_label.configure(text=f"Saving to: {save_destination}")


def add_folder():
    folder_path = filedialog.askdirectory(title="Select Folder to add to Backup List")
    if folder_path:
        if folder_path not in selected_folders:
            selected_folders.append(folder_path)
            textbox.insert("end", folder_path + "\n")
            with open(CONFIG_FILE, "a") as f:
                f.write(folder_path + "\n")
            status_label.configure(text=f"Added: {os.path.basename(folder_path)}", text_color="#10b981")
        else:
            status_label.configure(text="Folder already in backup list", text_color="#f59e0b")


def clear_list():
    selected_folders.clear()
    textbox.delete("0.0", "end")
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)
    status_label.configure(text="List cleared.", text_color="#d4d4d8")


def update_progress(pct):
    progress_bar.set(pct / 100.0)
    percentage_label.configure(text=f"{pct}%")


def update_status_text(text):
    status_label.configure(text=text)


def cancel_backup():
    global cancel_requested, is_running
    if not is_running:
        return
    cancel_requested = True
    status_label.configure(text="Cancelling process...", text_color="#f59e0b")
    try:
        CREATE_NO_WINDOW = 0x08000000
        subprocess.run(["taskkill", "/f", "/im", "rar.exe"], creationflags=CREATE_NO_WINDOW)
    except Exception:
        pass


def zip_worker():
    global is_running, cancel_requested, current_backup_path
    try:
        app.after(0, update_progress, 0)
        cancel_requested = False

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_name = os.path.join(save_destination, f"Emergency_Backup_{timestamp}.rar")
        current_backup_path = backup_name

        command = [winrar_exe_path, "a", backup_name] + selected_folders
        CREATE_NO_WINDOW = 0x08000000

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            creationflags=CREATE_NO_WINDOW,
            bufsize=0
        )

        def extract_and_update_filename(regex_str, buffer_str):
            match_file = re.search(regex_str, buffer_str)
            if match_file:
                raw_name = match_file.group(1).strip().rstrip('\\/')
                fname = os.path.basename(raw_name) if raw_name else match_file.group(1).strip()
                if len(fname) > 40:
                    fname = fname[:37] + "..."
                app.after(0, update_status_text, f"Archiving: {fname}")

        output_buffer = ""
        while True:
            char_bytes = process.stdout.read(1)
            if not char_bytes and process.poll() is not None:
                break

            try:
                char = char_bytes.decode('utf-8', errors='ignore')
            except Exception:
                continue

            if char == '\b':
                if output_buffer:
                    output_buffer = output_buffer[:-1]
            elif char in ('\r', '\n'):
                stripped_buf = output_buffer.strip()
                if stripped_buf.endswith("OK"):
                    extract_and_update_filename(r'(?:Adding|Updating)\s+(.+?)\s+OK$', stripped_buf)
                output_buffer = ""
            else:
                output_buffer += char
                if char == '%':
                    match_pct = re.search(r'(\d+)%$', output_buffer)
                    if match_pct:
                        pct = int(match_pct.group(1))
                        if pct <= 100:
                            app.after(0, update_progress, pct)

                    extract_and_update_filename(r'(?:Adding|Updating)\s+(.+?)\s+\d+%$', output_buffer)

        if cancel_requested:
            time.sleep(0.5)
            if os.path.exists(current_backup_path):
                try:
                    os.remove(current_backup_path)
                except Exception:
                    pass
            is_running = False
            app.after(0, update_progress, 0)
            app.after(0, lambda: update_status_text("Backup cancelled."))
            app.after(0, lambda: status_label.configure(text_color="#f59e0b"))
            app.after(0, lambda: run_btn.configure(state="normal"))
            app.after(0, lambda: cancel_btn.configure(state="disabled"))
            return

        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, command)

        app.after(0, update_progress, 100)

        if delete_old_switch.get() == 1:
            all_backups = []
            for file in os.listdir(save_destination):
                if file.startswith("Emergency_Backup_") and file.endswith(".rar"):
                    all_backups.append(os.path.join(save_destination, file))

            if len(all_backups) > 1:
                all_backups.sort()
                for old_backup in all_backups[:-1]:
                    try:
                        os.remove(old_backup)
                    except Exception:
                        pass

        is_running = False
        app.after(0, lambda: update_status_text("Success! Backup completed."))
        app.after(0, lambda: status_label.configure(text_color="#10b981"))
        app.after(0, lambda: run_btn.configure(state="normal"))
        app.after(0, lambda: cancel_btn.configure(state="disabled"))

    except subprocess.CalledProcessError:
        is_running = False
        app.after(0, update_progress, 0)
        app.after(0, lambda: update_status_text("Error: WinRAR failed to compress."))
        app.after(0, lambda: status_label.configure(text_color="#ef4444"))
        app.after(0, lambda: run_btn.configure(state="normal"))
        app.after(0, lambda: cancel_btn.configure(state="disabled"))
    except Exception:
        is_running = False
        app.after(0, update_progress, 0)
        app.after(0, lambda: update_status_text("An unexpected error occurred."))
        app.after(0, lambda: status_label.configure(text_color="#ef4444"))
        app.after(0, lambda: run_btn.configure(state="normal"))
        app.after(0, lambda: cancel_btn.configure(state="disabled"))


def create_backup():
    global winrar_exe_path, is_running

    if not selected_folders:
        status_label.configure(text="Error: No folders selected!", text_color="#ef4444")
        return

    if not winrar_exe_path or not os.path.exists(winrar_exe_path):
        winrar_exe_path = find_winrar()

        if not winrar_exe_path:
            status_label.configure(text="Please locate Rar.exe...", text_color="#f59e0b")
            app.update()

            winrar_exe_path = filedialog.askopenfilename(
                title="Locate Rar.exe",
                filetypes=[("Executable", "*.exe"), ("All Files", "*.*")]
            )

            if not winrar_exe_path:
                status_label.configure(text="Error: WinRAR needed to continue.", text_color="#ef4444")
                return

    is_running = True
    status_label.configure(text="Initializing...", text_color="#3b82f6")
    run_btn.configure(state="disabled")
    cancel_btn.configure(state="normal")

    threading.Thread(target=zip_worker, daemon=True).start()


change_dest_btn.configure(command=change_destination)
add_btn.configure(command=add_folder)
clear_btn.configure(command=clear_list)
run_btn.configure(command=create_backup)
cancel_btn.configure(command=cancel_backup)

load_saved_folders()
fade_in_window()
app.mainloop()