from config.load_config import config
import logging

import uuid


class MyLogger(logging.Logger):
    def __init__(self, name, level=logging.NOTSET):
        super().__init__(name, level)
        self.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s : %(levelname)s : %(name)s : %(message)s')
        handler.setFormatter(formatter)
        self.addHandler(handler)
        self.propagate = False

    def save_image(self, image_data: bytes) -> str:
        dir = config['GENERATED_IMAGE_OUTDIR']
        image_filename = str(uuid.uuid4())
        with open(f'{dir}/{image_filename}.jpg', 'wb') as f:
            f.write(image_data)
        self.info(f'Saved image: {image_filename}.jpg')
        return image_filename
