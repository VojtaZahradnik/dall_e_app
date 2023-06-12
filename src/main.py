import os
import sys
import yaml
from image_gen import ImageGen

# TODO: logging
# TODO: image name is right?
# TODO: mega testing!
# TODO: streamlit

def load_config(path: str) -> dict:
    with open(path, 'r') as file:
        return yaml.safe_load(file)

def main():
    image_gen = ImageGen(key=creds["DEEPAI_API_KEY"], conf=conf)
    image_gen.gen_image(prompt="put me on the moon")
    image_gen.save_image()

if __name__ == "__main__":

    conf = load_config("../configs/conf.yaml")
    creds = load_config("../configs/creds.yaml")

    sys.exit(main())
