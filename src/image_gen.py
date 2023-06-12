import requests
import os
from datetime import datetime

class ImageGen:

    def __init__(self, key: str) -> None:
        self.api_key = key
        self.image = None

    def save_image(self, path="generated_imgs") -> bool:
        # TODO try catch return bool - exception handling
        self.image.save(os.path.join(path,datetime.now().strftime("%Y%m%d%H%M%S")))

    def gen_image(self, image_path: str, prompt: str) -> str:
        # TODO exception to bad request, api error, no internet

        return requests.post(
            "https://api.deepai.org/api/image-editor",
            files={
                'image': open(image_path, 'rb'),
                'text': prompt,
            },
            headers={'api-key': self.api_key}
        )


