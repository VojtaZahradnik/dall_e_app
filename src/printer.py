import win32print
from PIL import Image

PHYSICALWIDTH = 110
PHYSICALHEIGHT = 111

class Printer:

    def __init__(self):
        self.default_printer = win32print.GetDefaultPrinter ()

    def print_image(self, image):
        # Convert the image to a Windows bitmap
        bmp = image.convert("RGB").tobytes("raw", "BGR")

        # Open the printer
        hPrinter = win32print.OpenPrinter(self.default_printer)

        # Set the properties of the document
        job = win32print.StartDocPrinter(hPrinter, 1, ("test document", None, "RAW"))

        # Start a page
        win32print.StartPagePrinter(hPrinter)

        # Write the image data to the printer
        win32print.WritePrinter(hPrinter, bmp)
        # End the page
        win32print.EndPagePrinter(hPrinter)

        # End the document
        win32print.EndDocPrinter(hPrinter)

        # Close the printer
        win32print.ClosePrinter(hPrinter)