from flask import Flask, render_template, url_for, redirect, request
import yaml
from werkzeug.utils import secure_filename

from image_gen import ImageGen
from watchdog.observers import Observer
# from printer import print_image
from gmail_api import GmailAPI
import logging
from logging.handlers import RotatingFileHandler
import os
import pandas as pd
from file_handler import Handler
from datetime import datetime
import csv

app = Flask(__name__, template_folder='templates', static_folder='static')
app.jinja_env.auto_reload = True
app.config['SERVER_NAME'] = 'localhost:5000'
app.config['TEMPLATES_AUTO_RELOAD'] = True


class AdastraApp:

    def __init__(self):
        self.logger = None
        self.app = Flask(__name__, template_folder='templates', static_folder='static')
        self.setup_routes()
        self.setup_logging()

        self.app.config['SERVER_NAME'] = 'localhost:5001'
        self.app.config['TEMPLATES_AUTO_RELOAD'] = True

        # Initialize other necessary objects and variables
        self.selected_preset = 0
        self.conf = self.load_config(os.path.join("src", "configs", "conf.yaml"))
        self.creds = self.load_config(os.path.join("src", "configs", "creds.yaml"))
        self.presets = self.load_presets(path=
                                         os.path.join("src",
                                                      "static",
                                                      "presets",
                                                      "presets.csv"))
        # Create objects from classes
        self.image_gen = ImageGen(key=self.creds["DEEPAI_API_KEY"], conf=self.conf)
        self.email_sender = GmailAPI(conf=self.conf)

        self.observer_source = None
        self.handler_source = None
        self.observer_dest = None
        self.handler_dest = None

    def setup_routes(self):
        self.app.add_url_rule("/", "home", self.home)
        self.app.add_url_rule("/send_email", "send_email", self.send_email, methods=["POST"])
        self.app.add_url_rule("/delete", "delete", self.delete, methods=["POST"])
        self.app.add_url_rule("/print", "send_to_printer", self.send_to_printer, methods=["POST"])
        self.app.add_url_rule("/upload", "upload", self.upload, methods=["POST"])
        self.app.add_url_rule("/generate", "generate", self.generate, methods=["POST"])
        self.app.add_url_rule("/selected-image", "handle_selected_image", self.handle_selected_image, methods=["POST"])

    def run(self, host='localhost', port=5001, debug=True):
        self.app.run(host, port, debug)

    def start_observers(self):
        # Start observers for source and destination folders
        # Source folder
        self.observer_source = Observer()
        self.handler_source = Handler(app=self.app, placeholder=self.conf["img_placeholder_before"])
        self.observer_source.schedule(self.handler_source, path=self.conf["img_source"], recursive=False)
        self.observer_source.start()
        self.app.logger.info(f"Observer for source folder {self.conf['img_source']} started")

        # Destination folder
        self.observer_dest = Observer()
        self.handler_dest = Handler(app=self.app, placeholder=self.conf["img_placeholder_edited"])
        self.observer_dest.schedule(self.handler_dest, path=self.conf["img_dest"], recursive=False)
        self.observer_dest.start()
        self.app.logger.info(f"Observer for destination folder {self.conf['img_dest']} started")

    def home(self):
        return render_template('index.html',
                               name_source=self.handler_source.img_path.replace("src", ""),
                               name_dest=self.handler_dest.img_path.replace("src", ""))

    def send_email(self):
        # Handle sending email
        if not os.path.exists("history"):
            os.mkdir("history")
        with open(os.path.join("history", "history.csv"), 'a') as f:
            writer = csv.writer(f)
            writer.writerow([request.form.get('firstname'),
                             request.form.get('lastname'),
                             request.form.get('email'),
                             self.image_gen.filename.replace("source_cleaned", "dest")])
            f.close()

        if self.image_gen.image and request.form.get('email') != "":
            self.app.logger.info(f"Sending email to {request.form.get('email')} with image "
                  f"{self.handler_dest.img_path}")
            self.email_sender.send_email(image_path=self.handler_dest.img_path,
                                         email_to=request.form.get('email'))
            self.handler_source.img_path = self.conf["img_placeholder_before"]
            self.handler_dest.img_path = self.conf["img_placeholder_edited"]
            self.image_gen.image = None

            return redirect(url_for('home'))
        else:
            self.app.logger.warn("Image is not generated or email is not provided")

            return redirect(url_for('home'))

    def delete(self):
        self.handler_source.img_path = self.conf["img_placeholder_before"]
        self.handler_dest.img_path = self.conf["img_placeholder_edited"]
        self.image_gen.image = None

        return redirect(url_for('home'))

    def send_to_printer(self):
        # Handle printing action
        self.app.logger.info("Printing")
        if self.image_gen.image:
            # print_image(image_path=handler_dest.img_path)
            self.app.logger.info("Printing done")
            self.handler_source.img_path = self.conf["img_placeholder_before"]
            self.handler_dest.img_path = self.conf["img_placeholder_edited"]

            self.image_gen.image = None

            return redirect(url_for("home"))

    def upload(self):
        self.handler_source.img_path = self.conf["img_placeholder_before"]
        self.handler_dest.img_path = self.conf["img_placeholder_edited"]
        try:

            uploaded_file = request.files['uploaded-photo']
            file_path = os.path.join(self.conf["img_source"], uploaded_file.filename)
            uploaded_file.save(file_path)

            filename = os.path.join(self.conf["img_source"],
                                    secure_filename(request.files['uploaded-photo'].filename))
            self.image_gen.filename = filename
            self.handler_source.img_path = filename
        except AttributeError as e:
            self.app.logger.error(e)
            self.image_gen.filename = self.conf["img_placeholder_before"]
            self.handler_source.img_path = self.conf["img_placeholder_edited"]
        self.app.logger.info(f"Selected image: {filename}")

        return redirect(url_for('home'))

    def generate(self):
        # Handle image generation
        self.app.logger.info(f"Selected image: {self.selected_preset}")

        if self.selected_preset and "placeholder" not in self.handler_source.img_path:
            self.app.logger.info("Starting generation phase")
            self.image_gen.remove_bckgr(self.handler_source.img_path)
            self.image_gen.crop_image(self.handler_source.img_path)
            self.image_gen.enhanced_image(self.handler_source.img_path)
            self.image_gen.gen_image(prompt=
                                     self.presets.iloc[int(self.selected_preset)]["prompt"])
        return redirect(url_for('home'))

    def handle_selected_image(self):
        # Handle selection of image
        selected_image = request.form.get('image')

        if selected_image:
            self.selected_preset = int(selected_image)

        return redirect(url_for('home'))

    def load_presets(self, path: str) -> pd.DataFrame:
        # Load presets from CSV file
        return pd.read_csv(path, delimiter=";")

    def load_config(self, path: str):
        # Load configuration from YAML file
        with open(path, 'r') as file:
            return yaml.safe_load(file)

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

    def initialize_app(self):
        try:
            self.conf = self.load_config(os.path.join("src", "configs", "conf.yaml"))
            self.creds = self.load_config(os.path.join("src", "configs", "creds.yaml"))
            self.app.logger.info("Configs loaded")
        except FileNotFoundError as e:
            self.app.logger.error("Configs not found")
            self.app.logger.error(e)

            # Load presets
        try:
            self.presets = self.load_presets(path=os.path.join("src", "static", "presets", "presets.csv"))
            self.app.logger.info("Presets loaded")
        except FileNotFoundError:
            self.app.logger.error("Presets CSV file not found")

        self.image_gen = ImageGen(key=self.creds["DEEPAI_API_KEY"], conf=self.conf)
        self.app.logger.info("Object from ImageGen class created")

        self.app.logger.info("Object from Printer class created")

        self.email_sender = GmailAPI(conf=self.conf)
        self.app.logger.info("Object from GMailAPI class created")

        self.start_observers()

        self.run()


if __name__ == "__main__":
    app = AdastraApp()
    app.initialize_app()
