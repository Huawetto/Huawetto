import smtplib
import random
import string
from tkinter import *
from tkinter import filedialog, simpledialog
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from tkinter import messagebox
import threading
import time
import os

# List of senders and their passwords
senders = [
     {"email": "user1@libero.it", "password": "password1"},
    {"email": "user2@libero.it", "password": "password2"},
    {"email": "user3@libero.it", "password": "password3"},
    {"email": "user4@libero.it", "password": "password4"},
    {"email": "user5@libero.it", "password": "password5"},
    {"email": "user6@libero.it", "password": "password6"},
    {"email": "user7@libero.it", "password": "password7"},
    {"email": "user8@libero.it", "password": "password8"},
    {"email": "user9@libero.it", "password": "password9"}
]
# Initialize the list for attachments
attachments = []

# Function to send email
def send_email():
    selected_sender = random.choice(senders)
    sender_email = selected_sender['email']
    sender_password = selected_sender['password']
    
    recipients = recipient_entry.get().split(",")  # Multiple recipients separated by commas
    subject = subject_entry.get()
    body = body_entry.get("1.0", END)
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    # Attach files
    for file_info in attachments:
        file = file_info['path']
        try:
            # Check file size (max 25 MB)
            if os.path.getsize(file) > 25 * 1024 * 1024:
                raise Exception(f"File {file} exceeds 25MB size limit.")
            
            part = MIMEBase('application', 'octet-stream')
            with open(file, 'rb') as f:
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{file_info["name"]}"')
            msg.attach(part)
        except Exception as e:
            messagebox.showerror("Error", f"Error attaching file {file}: {e}")
            return

    try:
        server = smtplib.SMTP_SSL('smtp.libero.it', 465)
        server.login(sender_email, sender_password)
        text = msg.as_string()

        for recipient in recipients:
            msg['To'] = recipient.strip()  # Removes extra spaces
            server.sendmail(sender_email, recipient.strip(), text)
            print(f"Email sent to {recipient.strip()} from {sender_email} successfully!")
            
        server.quit()
    except Exception as e:
        print(f"Error sending email: {e}")
        messagebox.showerror("Error", f"Error sending email: {e}")

# Function to add attachments
def add_attachments():
    files = filedialog.askopenfilenames(title="Select files", filetypes=(("All Files", "*.*"),))
    for file in files:
        # Check file size (must be <= 25 MB)
        if os.path.getsize(file) <= 25 * 1024 * 1024:
            attachment_info = {"path": file, "name": os.path.basename(file)}
            attachments.append(attachment_info)
            update_attachment_listbox()
        else:
            messagebox.showerror("Error", f"File {file} exceeds 25MB and won't be attached.")

# Function to update the attachment listbox
def update_attachment_listbox():
    attachment_listbox.delete(0, END)
    for i, file_info in enumerate(attachments):
        attachment_listbox.insert(END, f"{file_info['name']}")

# Function to remove an attachment
def remove_attachment():
    try:
        selected_index = attachment_listbox.curselection()[0]
        del attachments[selected_index]
        update_attachment_listbox()
    except IndexError:
        messagebox.showwarning("Warning", "Please select an attachment to remove.")

# Function to rename an attachment
def rename_attachment():
    try:
        selected_index = attachment_listbox.curselection()[0]
        new_name = simpledialog.askstring("Rename File", "Enter new filename:")
        if new_name:
            attachments[selected_index]['name'] = new_name
            update_attachment_listbox()
    except IndexError:
        messagebox.showwarning("Warning", "Please select an attachment to rename.")

# Function for sending emails with delay
def auto_click():
    while auto_click_enabled.get():
        send_email()
        time.sleep(delay_slider.get())  # Set delay in seconds between emails

# Toggle auto-click functionality
def toggle_auto_click():
    if auto_click_enabled.get():
        threading.Thread(target=auto_click, daemon=True).start()

# Function to generate random strings
def generate_random_string(length):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for _ in range(length))

# Function to generate random subject
def generate_random_subject():
    subject_entry.delete(0, END)
    subject_entry.insert(0, generate_random_string(50))

# Function to generate random body
def generate_random_body():
    body_entry.delete("1.0", END)
    body_entry.insert(END, generate_random_string(500))

# Create the main window
root = Tk()
root.title("Email Sender")
root.geometry("600x730")

# Recipients
recipient_label = Label(root, text="Recipients (comma separated):")
recipient_label.pack(pady=5)
recipient_entry = Entry(root, width=50)
recipient_entry.pack(pady=5)

# Subject
subject_label = Label(root, text="Subject:")
subject_label.pack(pady=5)
subject_entry = Entry(root, width=50)
subject_entry.pack(pady=5)
generate_subject_button = Button(root, text="Random Subject", command=generate_random_subject)
generate_subject_button.pack(pady=5)

# Body
body_label = Label(root, text="Body:")
body_label.pack(pady=5)
generate_body_button = Button(root, text="Random Body", command=generate_random_body)
generate_body_button.pack(pady=5)
body_entry = Text(root, height=10, width=50)
body_entry.pack(pady=5)

# Slider for delay between emails
delay_label = Label(root, text="Delay (seconds):")
delay_label.pack(pady=5)
delay_slider = Scale(root, from_=0.01, to=5, resolution=0.01, orient=HORIZONTAL)
delay_slider.set(1)  # Set a default value
delay_slider.pack(pady=5)

# Define auto_click_enabled as a BooleanVar
auto_click_enabled = BooleanVar()

# Auto-send checkbox
auto_click_checkbox = Checkbutton(root, text="Auto-send", variable=auto_click_enabled, command=toggle_auto_click)
auto_click_checkbox.pack(pady=5)

# Attachments
attachment_label = Label(root, text="Attachments (Max 25MB each):")
attachment_label.pack(pady=5)
attachment_listbox = Listbox(root, height=5, width=50)
attachment_listbox.pack(pady=5)

# Frame for managing attachments
attachment_button_frame = Frame(root)
attachment_button_frame.pack(pady=5)

add_attachment_button = Button(attachment_button_frame, text="Add Attachment", command=add_attachments)
add_attachment_button.grid(row=0, column=0)

rename_attachment_button = Button(attachment_button_frame, text="Rename Attachment", command=rename_attachment)
rename_attachment_button.grid(row=0, column=1)

remove_attachment_button = Button(attachment_button_frame, text="Remove Attachment", command=remove_attachment)
remove_attachment_button.grid(row=0, column=2)

# Send button
send_button = Button(root, text="Send", command=send_email)
send_button.pack(pady=10)

# Start the GUI
root.mainloop()
