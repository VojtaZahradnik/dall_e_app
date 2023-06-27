import os
from datetime import datetime
from PIL import Image
from io import BytesIO
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

        image_path = os.path.join("src", "static", self.conf.img_folders["croped"], f"{self.filename}.{self.conf.source_file_type}")

        image = Image.open(image_path)
        new_image = Image.new("RGBA", image.size, "WHITE")  # Create a white rgba background
        new_image.paste(image, (0, 0),
                        image)  # Paste the image on the background. Go to the links given below for details.
        new_image.convert('RGB').save(image_path, "PNG")

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


        try:
            name = f'{datetime.now().strftime("%Y%m%d%H%M%S")}.{self.conf.source_file_type}'
            self.save_image(url=self.image["output_url"],
                            path=os.path.join("src", "static", self.conf.img_folders["dest"]),
                            name=name)

            self.filename=name
        except AttributeError:
            self.app.logger.error("Image not generated properly")
        except TypeError:
            self.app.logger.error("Image is not returned")

        self.app.logger.info(f"Image generated with {prompt}")

    def remove_bckgr(self):

        image_path = os.path.join("src", "static", self.conf.img_folders["source"], self.filename)

        self.app.logger.info(f"Remove background: {image_path}")
        with open(image_path, 'rb') as file:
            input_image = file.read()

        output_image = rembg.remove(input_image)

        self.filename = os.path.splitext(self.filename)[0]

        # Save the result
        with open(os.path.join("src", "static", self.conf.img_folders["cleaned"], f"{self.filename}.{self.conf.source_file_type}"), "wb") as file:
            file.write(output_image)

    def crop_image(self):
        import numpy as np
        image_path = os.path.join("src", "static", self.conf.img_folders["cleaned"], f"{self.filename}.{self.conf.source_file_type}")
        image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)

        # Extract the alpha channel
        alpha = image[:, :, 3]

        # Find the non-transparent regions
        coords = np.argwhere(alpha > 0)
        y_min, x_min = coords.min(axis=0)
        y_max, x_max = coords.max(axis=0)

        # Crop the image to the non-transparent region
        cropped_image = image[y_min:y_max + 1, x_min:x_max + 1]

        # Save the cropped image
        cropped_image_path = os.path.join("src", "static", self.conf.img_folders["croped"],
                                          f"{self.filename}.{self.conf.source_file_type}")
        cv2.imwrite(cropped_image_path, cropped_image)

    def enhanced_image(self):

        image_path = os.path.join("src", "static", self.conf.img_folders["croped"], f"{self.filename}.{self.conf.source_file_type}")

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

        # Open the background image and foreground image
        background_image = Image.open(self.conf.adastra_background)
        foreground_image = Image.open(os.path.join("src", "static",
                                                   self.conf.img_folders["dest"],
                                                   self.filename))

        # Calculate the dimensions for resizing the foreground image
        border_width = background_image.width - 2 * border_size
        border_height = background_image.height - 2 * border_size

        foreground_resized = foreground_image.resize((border_width, border_height))

        # Create a new composite image with transparent background and the same size as the background image
        composite_image = Image.new("RGBA", background_image.size)

        # Paste the background image onto the composite image
        composite_image.paste(background_image, (0, 0))

        # Calculate the position to paste the resized foreground image with the border
        paste_position = (border_size, border_size)

        # Paste the resized foreground image onto the composite image with the border
        composite_image.paste(foreground_resized, paste_position)

        # Save the composite image
        composite_image.save(os.path.join("src", "static",
                                          self.conf.img_folders['dest_bckg'],
                                          self.filename))



