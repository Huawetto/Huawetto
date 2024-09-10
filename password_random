import tkinter as tk
from tkinter import scrolledtext
import random
import string

# Function to split the username into first name and last name or handle emails
def split_username(username):
    if '@' in username:  # Handle email
        username = username.split('@')[0]  # Take the part before the domain
    if '.' in username:
        parts = username.split('.')
        first_name, last_name = parts[0], parts[1] if len(parts) > 1 else "user"
    elif '_' in username:
        parts = username.split('_')
        first_name, last_name = parts[0], parts[1] if len(parts) > 1 else "user"
    else:
        first_name, last_name = username[:len(username)//2], username[len(username)//2:]
    
    return first_name.capitalize(), last_name.capitalize()

# Function to generate a password based on the selected method
def generate_password(username, method):
    first_name, last_name = split_username(username)

    if method == "Common Passwords":
        common_passwords = [
            "123456", "password", "123456789", "qwerty", "abc123", "password1", "admin", "letmein"
        ]
        return random.choice(common_passwords)

    elif method == "First Name + Last Name":
        base_password = f"{first_name}.{last_name}" if random.choice([True, False]) else f"{first_name}{last_name}"
        if random.choice([True, False]):
            base_password += str(random.randint(1, 9999))
        return base_password

    elif method == "Password with Years":
        year = random.randint(1950, 2025)
        return f"{first_name}{year}"

    elif method == "Complex Passwords":
        return ''.join(random.choices(string.ascii_letters + string.digits + "._-", k=random.randint(8, 12)))

    elif method == "All Types":
        all_methods = ["Common Passwords", "First Name + Last Name", "Password with Years", "Complex Passwords"]
        return generate_password(username, random.choice(all_methods))

    else:
        return "password"

# Function to generate and display the password
def generate_random_password():
    username = username_entry.get()
    method = password_type.get()

    if not username:
        messagebox.showerror("Error", "Please enter a name or email!")
        return

    password = generate_password(username, method)
    output_area.insert(tk.END, f"Generated password: {password}\n")
    output_area.see(tk.END)

# Creating the graphical interface
root = tk.Tk()
root.title("Password Randomizer")

# Frame for username (accepts email as well)
username_label = tk.Label(root, text="Name or Email:")
username_label.pack(pady=5)
username_entry = tk.Entry(root, width=50)
username_entry.pack(pady=5)

# Dropdown menu to select the password type
password_type_label = tk.Label(root, text="Password Type:")
password_type_label.pack(pady=5)

password_type = tk.StringVar(root)
password_type.set("Common Passwords")  # Default selection

password_menu = tk.OptionMenu(root, password_type, "Common Passwords", "First Name + Last Name", "Password with Years", "Complex Passwords", "All Types")
password_menu.pack(pady=5)

# Output area
output_area = scrolledtext.ScrolledText(root, width=70, height=20)
output_area.pack(pady=5)

# Button to generate the password
generate_button = tk.Button(root, text="Generate Password", command=generate_random_password)
generate_button.pack(pady=10)

# Start the GUI
root.mainloop()
