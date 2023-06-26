import os
from struct import Struct
import yaml
from collections import namedtuple
from flask import Flask
import pandas as pd
import csv


def create_folders(app: Flask, conf: Struct, path=os.path.join("src", "static")) -> None:
    folders = os.listdir(path)

    for folder in conf.img_folders.values():

        if folder not in folders:
            app.logger.info(f"Creating {folder}")
            os.mkdir(os.path.join("src", "static", folder))


def load_config(app: Flask, path: str) -> Struct:
    # Load configuration from YAML file
    try:
        with open(path) as file:
            config = yaml.load(file, Loader=yaml.FullLoader)
            app.logger.info(f"Config from {path} loaded")
            return namedtuple('Struct', config.keys())(*config.values())
    except FileNotFoundError as e:
        app.logger.error("Configs not ffound")
        app.logger.error(e)


def load_presets(app: Flask, path: str) -> pd.DataFrame:
    # Load presets from CSV file
    try:
        presets = pd.read_csv(path, delimiter=";")
        app.logger.info(f"Presets loaded from {path}")
        return presets
    except FileNotFoundError:
        app.logger.error("Presets CSV file not found")


def write_history(app: Flask,  email: str,
                  filename: str) -> None:

    app.logger.info("Writing data into history")
    with open(os.path.join("history", "history.csv"), 'a') as f:
        writer = csv.writer(f)
        writer.writerow([email,
                         filename])
        f.close()
