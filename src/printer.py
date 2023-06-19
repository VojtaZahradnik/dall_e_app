import win32printing
import subprocess


def print_image(image_path: str):
    try:
        subprocess.run(['mspaint.exe', '/pt', image_path], check=True)
        print("Printing image")
    except subprocess.CalledProcessError as e:
        print("Printing failed")
        print(e)
