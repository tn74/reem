from reem.datatypes import *
from reem.connection import *
from threading import Thread
import numpy as np
import time


TIME_TO_RUN = 5.0  # seconds


class Camera(Thread):
    def __init__(self, interface):
        self.publisher = PublishSpace(interface=interface)
        self.images_sent = 0
        super().__init__()

    def send_image(self):
        image = np.random.rand(640, 480, 3)
        self.publisher["raw_image"] = {"image": image, "id": self.images_sent}

    def run(self):
        start_time = time.time()
        while time.time() < start_time + TIME_TO_RUN:
            self.send_image()
            self.images_sent += 1
            print("Image {} Sent".format(self.images_sent))


class ImageProcessor(Thread):
    def __init__(self, interface):
        self.subscriber = CallbackSubscriber(channel="raw_image",
                                             interface=interface,
                                             callback_function=self.process_image,
                                             kwargs={})
        self.subscriber.listen()
        self.publisher = PublishSpace(interface=interface)
        super().__init__()

    def process_image(self, data, updated_path):
        print("Image {} Read".format(data["id"]))
        processed_data = {"id": data["id"], "mean": np.nanmean(data["image"])}
        self.publisher["processed_data"] = processed_data

    def run(self):
        start_time = time.time()
        while time.time() < start_time + TIME_TO_RUN:
            time.sleep(0.1)


class DataActor(Thread):
    def __init__(self, interface):
        self.subscriber = CallbackSubscriber(channel="processed_data",
                                             interface=interface,
                                             callback_function=self.actuation,
                                             kwargs={})
        self.subscriber.listen()
        self.publisher = PublishSpace(interface=interface)
        super().__init__()

    def actuation(self, data, updated_path):
        print("Acted on {}".format(data))

    def run(self):
        start_time = time.time()
        while time.time() < start_time + TIME_TO_RUN:
            time.sleep(0.1)


if __name__ == "__main__":
    interface = RedisInterface(host='localhost')

    camera = Camera(interface)
    processor = ImageProcessor(interface)
    actor = DataActor(interface)

    processor.start()
    camera.start()
    actor.start()

