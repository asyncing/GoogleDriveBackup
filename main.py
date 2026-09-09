import customtkinter as ctk
from customtkinter import filedialog
import os
import datetime
import threading
import subprocess
import winreg

save_destination = os.path.join(os.path.expanduser("~"), "Desktop")
selected_folders = []
CONFIG_FILE = "backup_folders.txt"
winrar_exe_path = None

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Emergency Backup Tool")
app.geometry("550x500")

dest_label = ctk.CTkLabel(app, text=f"Saving to: {save_destination}", font=("Arial", 12))
dest_label.pack(pady=(10, 0))

change_dest_btn = ctk.CTkButton(app, text="Change Save Location", fg_color="#6c757d", hover_color="#5a6268")
change_dest_btn.pack(pady=5)

delete_old_switch = ctk.CTkSwitch(app, text="Delete old backups after running")
delete_old_switch.pack(pady=10)

title_label = ctk.CTkLabel(app, text="Select Folders to Backup", font=("Arial", 20, "bold"))
title_label.pack(pady=(20, 10))

textbox = ctk.CTkTextbox(app, width=450, height=150)
textbox.pack(pady=10)

button_frame = ctk.CTkFrame(app, fg_color="transparent")
button_frame.pack(pady=10)

add_btn = ctk.CTkButton(button_frame, text="+ Add Folder", fg_color="#28a745", hover_color="#218838")
add_btn.grid(row=0, column=0, padx=10)

clear_btn = ctk.CTkButton(button_frame, text="Clear List", fg_color="#dc3545", hover_color="#c82333")
clear_btn.grid(row=0, column=1, padx=10)

progress_bar = ctk.CTkProgressBar(app, width=450)
progress_bar.pack(pady=10)
progress_bar.set(0)

run_btn = ctk.CTkButton(app, text="RUN BACKUP NOW", font=("Arial", 16, "bold"), width=450, height=40)
run_btn.pack(pady=10)

status_label = ctk.CTkLabel(app, text="Ready.", font=("Arial", 14))
status_label.pack(pady=10)


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
            status_label.configure(text=f"Added: {os.path.basename(folder_path)}", text_color="white")
        else:
            status_label.configure(text="Folder already in backup list", text_color="orange")


def clear_list():
    selected_folders.clear()
    textbox.delete("0.0", "end")
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)
    status_label.configure(text="List cleared.", text_color="white")


def zip_worker():
    try:
        progress_bar.configure(mode="indeterminate")
        progress_bar.start()

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_name = os.path.join(save_destination, f"Emergency_Backup_{timestamp}.rar")

        command = [winrar_exe_path, "a", backup_name] + selected_folders

        CREATE_NO_WINDOW = 0x08000000
        subprocess.run(command, check=True, creationflags=CREATE_NO_WINDOW)

        progress_bar.stop()
        progress_bar.configure(mode="determinate")
        progress_bar.set(1)

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

        status_label.configure(text="Success! Backup saved via WinRAR.", text_color="green")

    except subprocess.CalledProcessError:
        progress_bar.stop()
        progress_bar.configure(mode="determinate")
        progress_bar.set(0)
        status_label.configure(text="Error: WinRAR failed to compress the files.", text_color="red")
    except Exception as e:
        progress_bar.stop()
        progress_bar.configure(mode="determinate")
        progress_bar.set(0)
        status_label.configure(text=f"Error: {str(e)}", text_color="red")


def create_backup():
    global winrar_exe_path

    if not selected_folders:
        status_label.configure(text="Error: No folders selected!", text_color="red")
        return

    if not winrar_exe_path or not os.path.exists(winrar_exe_path):
        winrar_exe_path = find_winrar()

        if not winrar_exe_path:
            status_label.configure(text="Please locate Rar.exe...", text_color="orange")
            app.update()

            winrar_exe_path = filedialog.askopenfilename(
                title="Locate Rar.exe",
                filetypes=[("Executable", "*.exe"), ("All Files", "*.*")]
            )

            if not winrar_exe_path:
                status_label.configure(text="Error: Backup cancelled. WinRAR needed.", text_color="red")
                return

    status_label.configure(text="Zipping... Please wait...", text_color="yellow")
    progress_bar.set(0)
    threading.Thread(target=zip_worker, daemon=True).start()


change_dest_btn.configure(command=change_destination)
add_btn.configure(command=add_folder)
clear_btn.configure(command=clear_list)
run_btn.configure(command=create_backup)

load_saved_folders()
app.mainloop()