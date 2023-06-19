import win32printing
from PIL import Image
from subprocess import CalledProcessError, run

PHYSICALWIDTH = 110
PHYSICALHEIGHT = 111

class Printer:

    def __init__(self):
        pass
        # self.default_printer = win32print.GetDefaultPrinter ()

    def print_image(self, img_path: str):
        try:
            run(["mspaint.exe","/pt", img_path])