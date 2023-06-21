import win32printing
import subprocess


def print_image(image_path: str, orientation: int = 1):
    try:
        subprocess.run(['mspaint.exe', '/pt', image_path], check=True)

        # Get the default printer
        default_printer = win32printing.GetDefaultPrinter()

        # Open a handle to the printer
        printer_handle = win32printing.OpenPrinter(default_printer)

        # Set the job information, including the orientation
        job_info = {"pDevMode": win32printing.DocumentProperties(0, default_printer, None).Get(),
                    "pOrientation": orientation}
        win32printing.SetJob(printer_handle, 1, job_info, 0)

        # Close the printer handle
        win32printing.ClosePrinter(printer_handle)

        print("Printing image")
    except subprocess.CalledProcessError as e:
        print("Printing failed")
        print(e)