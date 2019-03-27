from reem import datatypes, ships, supports
from threading import Thread
import numpy as np
import time


class Camera(Thread):
    def __init__(self, interface):
        self.publisher = datatypes.PublishSpace(interface=interface)
        self.images_sent = 0
        super().__init__()

    def send_image(self):
        image = np.random.rand(640, 480, 3)
        self.publisher["raw_image"] = {"image": image, "id": self.images_sent}

    def run(self):
        while True:
            self.send_image()
            self.images_sent += 1
            time.sleep(1.0/30)  # 30 FPS


class ImageProcessor(Thread):
    def __init__(self, interface):
        self.processor = datatypes.PublishSpace(interface=interface)
        self.images_read = 0
        super().__init__()





