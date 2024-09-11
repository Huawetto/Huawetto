import tkinter as tk
from tkinter import filedialog, messagebox
import os
import subprocess

# Function to create the EXE file
def create_exe():
    script_content = script_text.get("1.0", tk.END).strip()
    exe_name = exe_name_entry.get().strip()
    package_name = package_name_entry.get().strip()
    version = version_entry.get().strip()
    author = author_entry.get().strip()
    icon_path = icon_path_entry.get().strip()

    if not script_content:
        messagebox.showerror("Error", "Please enter the script content!")
        return
    
    if not exe_name:
        messagebox.showerror("Error", "Please enter the EXE name!")
        return

    # Create a directory named after the exe_name if it doesn't exist
    exe_dir = os.path.join(os.getcwd(), exe_name)
    if not os.path.exists(exe_dir):
        os.makedirs(exe_dir)
    
    # Write the script content to a temporary .py file inside the exe folder
    script_file_path = os.path.join(exe_dir, f"{exe_name}.py")
    with open(script_file_path, "w") as script_file:
        script_file.write(script_content)
    
    # Build the PyInstaller command to create the EXE inside the exe folder
    command = ["pyinstaller", "--onefile", "--distpath", exe_dir]

    if icon_path:
        command.append(f"--icon={icon_path}")

    command.append(script_file_path)
    
    try:
        # Run PyInstaller to create the .exe in the target folder
        subprocess.run(command, check=True)
        messagebox.showinfo("Success", f"Executable '{exe_name}.exe' created successfully in folder '{exe_dir}'!")
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Error", f"Failed to create EXE: {e}")
    finally:
        # Clean up temporary script file generated by PyInstaller (the .spec file and build folder can be left for debugging if needed)
        spec_file = os.path.join(os.getcwd(), f"{exe_name}.spec")
        if os.path.exists(script_file_path):
            os.remove(script_file_path)
        if os.path.exists(spec_file):
            os.remove(spec_file)

# Function to browse for an icon file
def browse_icon():
    icon_file = filedialog.askopenfilename(
        title="Select Icon",
        filetypes=[("Icon Files", "*.png *.jpg *.jpeg")]
    )
    icon_path_entry.delete(0, tk.END)
    icon_path_entry.insert(0, icon_file)

# Create the main application window
root = tk.Tk()
root.title("EXE Creator")

# EXE name
tk.Label(root, text="EXE Name:").grid(row=0, column=0, padx=10, pady=10)
exe_name_entry = tk.Entry(root)
exe_name_entry.grid(row=0, column=1, padx=10, pady=10)

# Package name
tk.Label(root, text="Package Name:").grid(row=1, column=0, padx=10, pady=10)
package_name_entry = tk.Entry(root)
package_name_entry.grid(row=1, column=1, padx=10, pady=10)

# Version
tk.Label(root, text="Version:").grid(row=2, column=0, padx=10, pady=10)
version_entry = tk.Entry(root)
version_entry.grid(row=2, column=1, padx=10, pady=10)

# Author
tk.Label(root, text="Author:").grid(row=3, column=0, padx=10, pady=10)
author_entry = tk.Entry(root)
author_entry.grid(row=3, column=1, padx=10, pady=10)

# Script content
tk.Label(root, text="Script Content:").grid(row=4, column=0, padx=10, pady=10)
script_text = tk.Text(root, height=10, width=40)
script_text.grid(row=4, column=1, padx=10, pady=10)

# Icon path
tk.Label(root, text="Icon Path:").grid(row=5, column=0, padx=10, pady=10)
icon_path_entry = tk.Entry(root)
icon_path_entry.grid(row=5, column=1, padx=10, pady=10)
browse_icon_button = tk.Button(root, text="Browse", command=browse_icon)
browse_icon_button.grid(row=5, column=2, padx=10, pady=10)

# Create EXE button
create_exe_button = tk.Button(root, text="Create EXE", command=create_exe)
create_exe_button.grid(row=6, column=1, padx=10, pady=20)

# Start the Tkinter event loop
root.mainloop()
