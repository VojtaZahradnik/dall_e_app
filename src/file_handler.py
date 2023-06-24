from watchdog.events import FileSystemEventHandler
from flask import redirect, url_for

class Handler(FileSystemEventHandler):
    def __init__(self, app, placeholder):
        super().__init__()
        self.app = app
        self.img_path = placeholder
        with self.app.app_context():
            self.app.logger.info("Redirecting to home")

    def on_created(self, event):
        self.img_path = event.src_path
        print(f"Got event for {self.img_path}")

        with self.app.app_context():
            return redirect(url_for('home'))
