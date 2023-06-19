import win32printing
from PIL import Image
from subprocess import CalledProcessError

PHYSICALWIDTH = 110
PHYSICALHEIGHT = 111

class Printer:

    def __init__(self):
        pass
        # self.default_printer = win32print.GetDefaultPrinter ()

    def print_image(self, img_path: str):
        try:
            subprocess.run(["mspaint.exe","/pt", img_path])