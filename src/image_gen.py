import requests
import os
from datetime import datetime
from PIL import Image
from io import BytesIO
import glob


class ImageGen:

    def __init__(self, key: str, conf: dict) -> None:
        self.api_key = key
        self.conf = conf
        self.image = None

    def save_image(self) -> bool:
        # TODO: try catch return bool - exception handling
        response = requests.get(self.image["output_url"])
        image = Image.open(BytesIO(response.content))

        if not os.path.exists(self.conf["img_dest"]):
            os.mkdir(self.conf["img_dest"])

        image.save(os.path.join(self.conf["img_dest"],
                                f'{datetime.now().strftime("%Y%m%d%H%M%S")}.{self.conf["source_file_type"]}'),
                   "PNG")
        print("saved")

    def gen_image(self, prompt) -> str:
        # TODO: exception to bad request, api error, no internet

        print("gen. started")
        print(prompt)
        self.image = requests.post(
            self.conf["api_name"],
            files={
                'image': open(self.get_last_png(), 'rb'),
                'text': prompt,
            },
            headers={'api-key': self.api_key}
        ).json()
        print(self.image)
        print("gen. done")

    def get_last_png(self) -> str:

        if not os.path.exists(self.conf["img_source"]):
            os.mkdir(self.conf["img_source"])
            return 1

        png_files = glob.glob(os.path.join(self.conf["img_source"],
                                           f'*.{self.conf["source_file_type"]}'))
        png_files.sort(key=os.path.getmtime)
        print(png_files[-1])
        return png_files[-1]
