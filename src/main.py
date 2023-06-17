from flask import Flask, render_template, request, url_for, redirect
import yaml
from image_gen import ImageGen
from tkinter.filedialog import askopenfilename
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from printer import Printer
from send_email import SendEmail
from datetime import datetime

app = Flask(__name__, template_folder='templates', static_folder='static')
app.jinja_env.auto_reload = True
app.config['SERVER_NAME'] = 'localhost:5000'
app.config['TEMPLATES_AUTO_RELOAD'] = True


class SourceHandler(FileSystemEventHandler):
    def __init__(self, app):
        self.app = app
        self.img_path = image_gen.filename
        print(self.img_path)
        with self.app.app_context():
            render_template("index.html", name_source=self.img_path)

    def on_created(self, event):
        self.img_path = event.src_path.replace("static/", "")
        print(f"Got event for {self.img_path}")
        with self.app.app_context():
            print(f"Changing source image to {self.img_path}")
            return render_template("index.html", name_source=self.img_path)


class DestHandler(FileSystemEventHandler):
    def __init__(self, app):
        self.app = app
        self.img_path = image_gen.filename
        with self.app.app_context():
            render_template("index.html", name_source=self.img_path)

    def on_created(self, event):
        self.img_path = event.src_path.replace("static/", "")
        print(f"Got event for {self.img_path}")
        with self.app.app_context():
            print(f"Changing destination image to {self.img_path}")
            return render_template("index.html", name_dest=self.img_path)


def load_config(path: str) -> dict:
    with open(path, 'r') as file:
        return yaml.safe_load(file)


@app.route("/")
def home():
    return render_template('index.html',
                           name_source=handler_source.img_path,
                           name_dest=handler_dest.img_path)


@app.route("/send_email", methods=["POST"])
def send_email():
    if image_gen.image:
        email_sender.send_mail()
        return render_template("index.html",
                               name_source=handler_source.img_path,
                               name_dest=handler_dest.img_path)


@app.route("/print", methods=["POST"])
def print_image():
    if image_gen.image:
        printer.print(image_gen.get_image())
        return render_template("index.html",
                               name_source=handler_source.img_path,
                               name_dest=handler_dest.img_path)


@app.route("/upload", methods=["POST"])
def upload():
    try:
        filename = askopenfilename(initialdir=conf["img_source"],
                                   title="Select a Image",
                                   filetypes=[
                                       ("image", ".jpeg"),
                                       ("image", ".png"),
                                       ("image", ".jpg"),
                                   ]).split("static")[-1]
    except AttributeError as e:
        print(e)
        filename = conf["img_placeholder"]
    print(f"Selected image: {filename}")

    image_gen.filename = filename
    return render_template("index.html",
                           name_source=filename,
                           name_dest=handler_dest.img_path)


@app.route("/generate", methods=["POST"])
def generate():
    image_gen.gen_image(prompt="Change my face into cyborg")
    image_gen.save_image()
    return render_template("index.html",
                           name_source=handler_source.img_path,
                           name_dest=handler_dest.img_path)


if __name__ == "__main__":
    conf = load_config("configs/conf.yaml")
    creds = load_config("configs/creds.yaml")
    print("Configs loaded")

    image_gen = ImageGen(key=creds["DEEPAI_API_KEY"], conf=conf)
    print("Object from ImageGen class created")

    printer = Printer()
    print("Object from Printer class created")

    email_sender = SendEmail(email_from=conf["email_from"],
                             email_to=conf["email_to"],
                             date=datetime.now(),
                             subject=conf["email_subject"],
                             server=conf["email_server"])
    print("Object from SendEmail class created")

    observer_source = Observer()
    handler_source = SourceHandler(app)
    observer_source.schedule(handler_source, path=conf["img_source"], recursive=False)
    observer_source.start()

    observer_dest = Observer()
    handler_dest = SourceHandler(app)
    observer_dest.schedule(handler_dest, path=conf["img_dest"], recursive=False)
    observer_dest.start()

    app.run(debug=True)
