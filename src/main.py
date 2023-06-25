from support import create_folders, load_config, load_presets, write_history
from flask import Flask, render_template, url_for, redirect, request
from werkzeug.utils import secure_filename
from image_gen import ImageGen
from watchdog.observers import Observer
from printer import print_image
from gmail_api import GmailAPI
import logging
from logging.handlers import RotatingFileHandler
import os
from file_handler import Handler
from datetime import datetime


class AdastraApp:

    def __init__(self):
        self.app = Flask(__name__, template_folder='templates', static_folder='static')
        self.app.config['TEMPLATES_AUTO_RELOAD'] = True
        self.setup_routes()
        self.setup_logging()

        # Initialize other necessary objects and variables
        self.selected_preset = None

        self.conf = load_config(app=self.app,
                                path=os.path.join("src", "configs", "conf.yaml"))
        self.creds = load_config(app=self.app,
                                 path=os.path.join("src", "configs", "creds.yaml"))

        self.app.config['SERVER_NAME'] = f'localhost:{self.conf.port}'


        self.presets = load_presets(app=self.app,
                                    path=os.path.join(
                                        "src",
                                        "static",
                                        self.conf.img_folders["presets"],
                                        "presets.csv"))

        self.observer_source = None
        self.handler_source = None
        self.observer_dest = None
        self.handler_dest = None
        self.image_gen = None
        self.email_sender = None
        self.logger = None

    def setup_routes(self):
        self.app.add_url_rule("/", "home", self.home)
        self.app.add_url_rule("/send_email", "send_email", self.send_email, methods=["POST"])
        self.app.add_url_rule("/delete", "delete", self.delete, methods=["POST"])
        self.app.add_url_rule("/print", "send_to_printer", self.send_to_printer, methods=["POST"])
        self.app.add_url_rule("/upload", "upload", self.upload, methods=["POST"])
        self.app.add_url_rule("/generate", "generate", self.generate, methods=["POST"])
        self.app.add_url_rule("/selected-image", "handle_selected_image", self.handle_selected_image, methods=["POST"])

    def run(self, host='localhost'):
        self.app.run(host, self.conf.port, self.conf.debug)

    def start_observers(self):
        # Start observers for source and destination folders
        # Source folder
        self.observer_source = Observer()
        self.handler_source = Handler(app=self.app, placeholder=self.conf.placeholders["before"])
        self.observer_source.schedule(self.handler_source, path=os.path.join("src",
                                                                             "static",
                                                                             self.conf.img_folders["source"]),
                                      recursive=False)
        self.observer_source.start()
        self.app.logger.info(
            f"Observer for source folder {os.path.join('src', 'static', self.conf.img_folders['source'])} started")

        # Destination folder
        self.observer_dest = Observer()
        self.handler_dest = Handler(app=self.app, placeholder=self.conf.placeholders["edited"])
        self.observer_dest.schedule(self.handler_dest, path=os.path.join("src",
                                                                         "static",
                                                                         self.conf.img_folders["dest"]),
                                    recursive=False)
        self.observer_dest.start()
        self.app.logger.info(
            f"Observer for destination folder {os.path.join('src', 'static', self.conf.img_folders['dest'])} started")

    def home(self):
        return render_template('index.html',
                               name_source=self.handler_source.img_path.split("src", 1)[-1],
                               name_dest=self.handler_dest.img_path.split("src", 1)[-1])

    def send_email(self):
        # Handle sending email
        if not os.path.exists("history"):
            os.mkdir("history")

        write_history(app=self.app,
                      firstname=request.form.get("firstname"),
                      lastname=request.form.get("lastname"),
                      email=request.form.get("email"),
                      filename=self.image_gen.filename.replace("source_cleaned", "dest"))

        if self.image_gen.image and request.form.get('email') != "":
            self.app.logger.info(f"Sending email to {request.form.get('email')} with image")
            self.email_sender.send_email(image_path=os.path.join("src", "static",
                                                                 self.conf.img_folders['dest_bckg'],
                                                                 os.path.basename(self.handler_dest.img_path)),
                                         email_to=request.form.get('email'))

            return redirect(url_for('home'))
        else:
            self.app.logger.warning("Image is not generated or email is not provided")

            return redirect(url_for('home'))

    def delete(self):
        self.handler_source.img_path = self.conf.placeholders["before"]
        self.handler_dest.img_path = self.conf.placeholders["edited"]
        self.image_gen.image = None

        return redirect(url_for('home'))

    def send_to_printer(self):
        # Handle printing action
        self.app.logger.info("Printing")
        if self.image_gen.image:
            print_image(image_path=os.path.join("src", "static",
                                                self.conf.img_folders['dest_bckg'],
                                                os.path.basename(self.handler_dest.img_path)))
            self.app.logger.info("Printing done")
            return redirect(url_for("home"))
        else:
            return redirect(url_for("home"))

    def upload(self):
        self.handler_source.img_path = self.conf.placeholders["before"]
        self.handler_dest.img_path = self.conf.placeholders["edited"]
        try:

            uploaded_file = request.files['uploaded-photo']
            file_path = os.path.join("src", "static",
                                     self.conf.img_folders["source"], uploaded_file.filename)
            uploaded_file.save(file_path)

            filename = os.path.join("src", "static",
                                    self.conf.img_folders["source"],
                                    secure_filename(request.files['uploaded-photo'].filename))
            self.image_gen.filename = filename
            self.handler_source.img_path = filename
        except AttributeError as e:
            self.app.logger.error(e)
            self.image_gen.filename = self.conf.placeholders["before"]
            self.handler_source.img_path = self.conf.placeholders["edited"]
        self.app.logger.info(f"Selected image: {filename}")

        return redirect(url_for('home'))

    def generate(self):
        # Handle image generation
        self.app.logger.info(f"Selected image: {self.selected_preset}")

        self.image_gen.filename = os.path.basename(self.handler_source.img_path)

        if self.selected_preset is not None and "placeholder" not in self.image_gen.filename:
            self.app.logger.info(f"Starting generation phase for {self.image_gen.filename}")
            self.image_gen.remove_bckgr()
            self.image_gen.crop_image()
            self.image_gen.enhanced_image()
            self.image_gen.gen_image(prompt=
                                     self.presets.iloc[int(self.selected_preset)]["prompt"])
            self.image_gen.add_background()

        return redirect(url_for('home'))

    def handle_selected_image(self):
        # Handle selection of image
        selected_image = request.form.get('image')

        if selected_image:
            self.selected_preset = int(selected_image)

        self.app.logger.info(f"Selected image from slider: {self.selected_preset}")

        return redirect(url_for('home'))

    def setup_logging(self):
        # Create a file handler for logging
        handler = RotatingFileHandler(f"logs/app_{datetime.now().strftime('%Y%m%d%H')}.log", maxBytes=10000,
                                      backupCount=0)
        handler.setLevel(logging.DEBUG)

        # Create a formatter for the log messages
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)

        # Add the file handler to the Flask app's logger
        self.app.logger.addHandler(handler)
        self.app.logger.setLevel(logging.DEBUG)

        self.app.logger.info("Logger setup done")

    def initialize_app(self):

        create_folders(app=self.app, conf=self.conf)

        self.image_gen = ImageGen(app=self.app, key=self.creds.DEEPAI_API_KEY,
                                  conf=self.conf)
        self.app.logger.info("Object from ImageGen class created")

        self.email_sender = GmailAPI(app=self.app, conf=self.conf)
        self.app.logger.info("Object from GMailAPI class created")

        self.start_observers()

        self.run()


if __name__ == "__main__":
    app = AdastraApp()
    app.initialize_app()
