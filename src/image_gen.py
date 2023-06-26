import os
from datetime import datetime
from PIL import Image
from io import BytesIO
import glob
import requests
import rembg
import cv2
from flask import Flask


class ImageGen:

    def __init__(self, app: Flask, key: str, conf: dict) -> None:
        self.api_key = key
        self.conf = conf
        self.image = None
        self.app = app
        self.filename = conf.placeholders["before"]

    def save_image(self, url: str, path: str, name: str) -> bool:
        self.app.logger.info(f"Saving image: {self.filename}")
        response = requests.get(url)
        image = Image.open(BytesIO(response.content))

        image.save(os.path.join(path,
                                name),
                   "PNG")
        self.filename = name
        self.app.logger.info("Image saved")

    def gen_image(self, prompt) -> str:

        image_path = os.path.join("src", "static", self.conf.img_folders["enhanced"], self.filename)

        self.app.logger.info(f"Starting gen. phase with {prompt} on {image_path}")
        try:
            self.image = requests.post(
                self.conf.api_name,
                files={
                    'image': open(image_path, 'rb'),
                    'text': prompt,
                },
                headers={'api-key': self.api_key}
            ).json()
        except FileNotFoundError:
            self.app.logger.error(f"{self.filename} not found")
        except KeyError as e:
            self.app.logger.error("Api error")
            self.app.logger.error(e)

        if not "output_url" in self.image.keys():
            self.app.logger.error("Generating of image failed. Not output url founded")
            return 1

        self.save_image(url=self.image["output_url"],
                        path=os.path.join("src", "static", self.conf.img_folders["dest"]),
                        name=f'{datetime.now().strftime("%Y%m%d%H%M%S")}.{self.conf.source_file_type}')

        self.app.logger.info(f"Image generated with {prompt}")

    def remove_bckgr(self):

        image_path = os.path.join("src", "static", self.conf.img_folders["source"], self.filename)

        self.app.logger.info(f"Remove background: {image_path}")
        with open(image_path, 'rb') as file:
            input_image = file.read()

        output_image = rembg.remove(input_image)

        # Save the result
        with open(os.path.join("src", "static", self.conf.img_folders["cleaned"], self.filename), 'wb') as file:
            file.write(output_image)

    def crop_image(self):

        image_path = os.path.join("src", "static", self.conf.img_folders["cleaned"], self.filename)

        self.app.logger.info(f"Croping: {image_path}")

        image = cv2.imread(image_path)

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        _, threshold = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)

        contours, _ = cv2.findContours(threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        largest_contour = max(contours, key=cv2.contourArea)

        x, y, w, h = cv2.boundingRect(largest_contour)

        cropped_image = image[y:y + h, x:x + w]

        # Save the cropped image
        cv2.imwrite(os.path.join("src", "static", self.conf.img_folders["croped"], self.filename), cropped_image)

    def enhanced_image(self):

        image_path = os.path.join("src", "static", self.conf.img_folders["croped"], self.filename)

        self.app.logger.info(f"Enhancing image: {image_path}")

        try:
            image = requests.post(
                "https://api.deepai.org/api/torch-srgan",
                files={
                    'image': open(image_path, 'rb')
                },
                headers={'api-key': self.api_key}
            ).json()
        except FileNotFoundError:
            self.app.logger.error(f"{self.filename} not found")
        except KeyError as e:
            self.app.logger.error("Api error")
            self.app.logger.error(e)
        except UnboundLocalError as e:
            self.app.logger.error("Variable not set")
            self.app.logger.error(e)

        self.save_image(url=image["output_url"],
                        path=os.path.join("src", "static",
                                          self.conf.img_folders["enhanced"]),
                        name=self.filename
                        )

    def add_background(self, border_size=100):

        background_image = Image.open(self.conf.adastra_background)
        foreground_image = Image.open(os.path.join("src", "static",
                                                   self.conf.img_folders["dest"],
                                                   self.filename))

        border_width = background_image.width - 2 * border_size
        border_height = background_image.height - 2 * border_size

        foreground_resized = foreground_image.resize((border_width, border_height))

        composite_image = Image.new("RGBA", background_image.size)
        composite_image.paste(background_image, (0, 0))

        paste_position = (border_size, border_size)

        composite_image.paste(foreground_resized, paste_position)

        composite_image.save(os.path.join("src", "static",
                                          self.conf.img_folders['dest_bckg'],
                                          self.filename
                                          ))
