import requests
import os
from datetime import datetime
from PIL import Image
from io import BytesIO
import glob
import requests
import rembg

class ImageGen:

    def __init__(self, key: str, conf: dict) -> None:
        self.api_key = key
        self.conf = conf
        self.image = None
        self.filename = conf["img_placeholder"]

    def save_image(self) -> bool:
        # TODO: try catch return bool - exception handling
        response = requests.get(self.image["output_url"])
        image = Image.open(BytesIO(response.content))

        if not os.path.exists(self.conf["img_dest"]):
            os.mkdir(self.conf["img_dest"])

        image.save(os.path.join(self.conf["img_dest"],
                                f'{datetime.now().strftime("%Y%m%d%H%M%S")}.'
                                f'{self.conf["source_file_type"]}'),
                   "PNG")
        print("Image saved")

    def gen_image(self, prompt) -> str:
        # TODO: exception to bad request, api error, no internet
        print(self.filename)
        if "source_cleaned" not in self.filename:
            self.filename = self.filename.replace("source", "source_cleaned")
        image_path = "src/static/" + self.filename

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

        print(f"Image generated with {prompt}")

    def get_last_png(self) -> str:

        if not os.path.exists(self.conf["img_source"]):
            print(f"Creating source folder in {self.conf['img_source']}")
            os.mkdir(self.conf["img_source"])

        png_files = glob.glob(os.path.join(self.conf["img_source"],
                                           f'*.{self.conf["source_file_type"]}'))

        if png_files == []:
            print(f"No files in source folder {self.conf['img_source']} founded")
            return []

        print(png_files)

        png_files.sort(key=os.path.getmtime)
        print(f"Last PNG: {png_files[-1]}")
        return png_files[-1]

    def get_image(self):
        response = requests.get(self.image["output_url"])
        return Image.open(BytesIO(response.content))

    def remove_bckgr(self, img_name: str):
        with open(f"src/static/{img_name}", 'rb') as file:
            input_image = file.read()

        output_image = rembg.remove(input_image)

        if not os.path.exists(self.conf['img_cleaned']):
            os.mkdir(self.conf['img_cleaned'])

        # Save the result
        with open(f"{self.conf['img_cleaned']}/{img_name.replace('source/','')}", 'wb') as file:
            file.write(output_image)



