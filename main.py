import customtkinter as ctk
from customtkinter import filedialog
import zipfile
import os
import datetime

save_destination=os.path.join(os.path.expanduser("~"), "Desktop")
selected_folders = []





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
            status_label.configure(text=f"Added: {os.path.basename(folder_path)}", text_color="white")
        else:
            status_label.configure(text="Folder already in backup list", text_color="orange")


def clear_list():

    selected_folders.clear()
    textbox.delete("0.0", "end")
    status_label.configure(text="List cleared.", text_color="white")


def create_backup():

    if not selected_folders:
        status_label.configure(text="Error: No folders selected!", text_color="red")
        return


    status_label.configure(text="Zipping... Please wait...", text_color="yellow")
    app.update()

    try:


        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        backup_name = os.path.join(save_destination, f"Emergency_Backup_{timestamp}.zip")


        with zipfile.ZipFile(backup_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for folder in selected_folders:
                for root, dirs, files in os.walk(folder):
                    for file in files:
                        file_path = os.path.join(root, file)

                        arcname = os.path.relpath(file_path, os.path.dirname(folder))
                        zipf.write(file_path, arcname)

        status_label.configure(text="Success! Zip saved to your Desktop.", text_color="green")

        if delete_old_switch.get() == 1:
            all_backups = []


            for file in os.listdir(save_destination):
                if file.startswith("Emergency_Backup_") and file.endswith(".zip"):
                    all_backups.append(os.path.join(save_destination, file))


            if len(all_backups) > 1:
                all_backups.sort()


                for old_backup in all_backups[:-1]:
                    try:
                        os.remove(old_backup)
                        print(f"Deleted old backup: {old_backup}")
                    except Exception as e:
                        print(f"Could not delete {old_backup}: {e}")

    except Exception as e:
        status_label.configure(text=f"Error: {str(e)}", text_color="red")


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")
app = ctk.CTk()
app.title("Emergency Backup Tool")
app.geometry("550x450")
dest_label = ctk.CTkLabel(app, text=f"Saving to: {save_destination}", font=("Arial", 12))
dest_label.pack(pady=(10, 0))
delete_old_switch = ctk.CTkSwitch(app, text="Delete old backups after running")
delete_old_switch.pack(pady=10)
change_dest_btn = ctk.CTkButton(app, text="Change Save Location", fg_color="#6c757d", hover_color="#5a6268")
change_dest_btn.pack(pady=5)
title_label = ctk.CTkLabel(app, text="Select Folders to Backup", font=("Arial", 20, "bold"))
title_label.pack(pady=(20, 10))
textbox = ctk.CTkTextbox(app, width=450, height=180)
textbox.pack(pady=10)
button_frame = ctk.CTkFrame(app, fg_color="transparent")
button_frame.pack(pady=10)
change_dest_btn.configure(command=change_destination)
add_btn = ctk.CTkButton(button_frame, text="+ Add Folder", command=add_folder, fg_color="#28a745",hover_color="#218838")
add_btn.grid(row=0, column=0, padx=10)
clear_btn = ctk.CTkButton(button_frame, text="Clear List", command=clear_list, fg_color="#dc3545",hover_color="#c82333")
clear_btn.grid(row=0, column=1, padx=10)
run_btn = ctk.CTkButton(app, text="RUN BACKUP NOW", command=create_backup, font=("Arial", 16, "bold"), width=450,height=40)
run_btn.pack(pady=10)
status_label = ctk.CTkLabel(app, text="Ready.", font=("Arial", 14))
status_label.pack(pady=10)
app.mainloop()