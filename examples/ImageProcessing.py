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
            # time.sleep(1.0/60)  # 30 FPS
            print("Image {} Sent".format(self.images_sent))


class ImageProcessor(Thread):
    def __init__(self, interface):
        self.subscriber = datatypes.UpdateSubscriber(top_key_name="raw_image", interface=interface)
        self.subscriber.listen()
        self.publisher = datatypes.PublishSpace(interface=interface)
        super().__init__()

    def process_images(self):
        while True:
            channel, message = self.subscriber.queue.get()
            self.subscriber.process_update(channel, message)
            data = self.subscriber.value()
            shape = data["image"].shape
            print("Image {} Read".format(data["id"]))

    def run(self):
        self.process_images()


if __name__ == "__main__":
    interface = supports.RedisInterface(ships=[ships.NumpyShip()])
    camera = Camera(interface)
    camera.setDaemon(True)
    processor = ImageProcessor(interface)
    processor.setDaemon(True)
    processor.start()
    camera.start()
    time.sleep(5)


