import os
import random
import string

def generate_random_name(length):
    """Generate a random name of specified length."""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def create_files(num_files, file_size, extensions):
    """Create files with specified sizes and random names."""
    for ext in extensions:
        for _ in range(num_files):
            random_name = generate_random_name(file_name_length)
            file_name = f"{random_name}.{ext}"
            with open(file_name, 'wb') as f:
                f.write(b'\0' * file_size)
            print(f"[SUCCESS] File created: {file_name}")

if __name__ == "__main__":
    # User input
    try:
        file_name_length = int(input("Enter the length of the file name: "))
        num_files = int(input("Enter the number of files to generate for each extension: "))
        file_size = int(input("Enter the file size in bytes: "))
        extensions = input("Enter file extensions separated by space (e.g., mp3 wav mp4 png): ").split()

        # File creation
        create_files(num_files, file_size, extensions)
        print("All files were generated successfully.")
    except ValueError:
        print("[ERROR] Please enter a valid value.")
