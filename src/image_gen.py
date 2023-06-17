import requests
import os
from datetime import datetime
from PIL import Image
from io import BytesIO
import glob
import requests

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

        if self.filename != "":
            image_path = "static" + self.filename
        else:
            image_path = self.get_last_png()

        print(f"Starting gen. phase with {prompt} on {image_path}")
        self.image = requests.post(
            self.conf["api_name"],
            files={
                'image': open(image_path, 'rb'),
                'text': prompt,
            },
            headers={'api-key': self.api_key}
        ).json()

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

        png_files.sort(key=os.path.getmtime)
        print(f"Last PNG: {png_files[-1]}")
        return png_files[-1]

    def get_image(self):
        response = requests.get(self.image["output_ulr"])
        return Image.open(BytesIO(response.content))


