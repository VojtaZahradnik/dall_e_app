import os
from datetime import datetime
from PIL import Image
from io import BytesIO
import glob
import requests
import rembg
import cv2

class ImageGen:

    def __init__(self, key: str, conf: dict) -> None:
        self.api_key = key
        self.conf = conf
        self.image = None
        self.filename = conf.placeholders["before"]

    def save_image(self, url: str, path: str, name: str) -> bool:
        # TODO: try catch return bool - exception handling
        print("Saving image: ", path + "/"+name)
        response = requests.get(url)
        image = Image.open(BytesIO(response.content))

        if not os.path.exists(self.conf.img_folders["dest"]):
            os.mkdir(self.conf.img_folders["dest"])

        print(os.path.join(path,
                                f'{name}.{self.conf.source_file_type}'))

        image.save(os.path.join(path,
                                f'{name}.{self.conf.source_file_type}'),
                   "PNG")
        print("Image saved")

    def gen_image(self, prompt, filename: str) -> str:
        # TODO: exception to bad request, api error, no internet
        self.filename = filename
        if "source_enhanced" not in self.filename:
            self.filename = self.filename.replace("source", "source_enhanced").replace(".jpg",".png")
        image_path = self.filename

        print(f"Starting gen. phase with {prompt} on {image_path}")
        try:
            self.image = requests.post(
                self.conf["api_name"],
                files={
                    'image': open(image_path, 'rb'),
                    'text': prompt,
                },
                headers={'api-key': self.api_key}
            ).json()
        except FileNotFoundError:
            print(f"{self.filename} not found")
        except KeyError as e:
            print("Api error")
            print(e)

        print(self.image)
        if not "output_url" in self.image.keys():
            print("Generating of image failed. Not output url founded")
            return 1

        self.save_image(url = self.image["output_url"],
                        path = self.conf["img_dest"],
                        name=f'{datetime.now().strftime("%Y%m%d%H%M%S")}.')

        print(f"Image generated with {prompt}")

    def remove_bckgr(self, img_path: str):
        print("Remove background: ", img_path)
        with open(img_path, 'rb') as file:
            input_image = file.read()

        output_image = rembg.remove(input_image)

        # Save the result
        with open(img_path.replace("source","source_cleaned"), 'wb') as file:
            file.write(output_image)

    def crop_image(self, image_path):

        image_path = image_path.replace("source","source_cleaned")

        print("Croping: ", image_path)

        image = cv2.imread(image_path)

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        _, threshold = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)

        contours, _ = cv2.findContours(threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        largest_contour = max(contours, key=cv2.contourArea)

        x, y, w, h = cv2.boundingRect(largest_contour)

        cropped_image = image[y:y + h, x:x + w]

        # Save the cropped image
        cv2.imwrite(image_path.replace("source_cleaned", "source_croped"), cropped_image)

    def enhanced_image(self, image_path):

        image_path = image_path.replace("source", "source_croped")

        print("Enhancing image: ", image_path)

        try:
            image = requests.post(
                "https://api.deepai.org/api/torch-srgan",
                files={
                    'image': open(image_path, 'rb')
                },
                headers={'api-key': self.api_key}
            ).json()
        except FileNotFoundError:
            print(f"{self.filename} not found")
        except KeyError as e:
            print("Api error")
            print(e)
        except UnboundLocalError as e:
            print("Variable not set")
            print(e)

        self.save_image(image["output_url"], name=os.path.split(image_path)[-1].split(".")[0],
        path = self.conf.img_folders["source"].replace("source","source_enhanced"))


