from threading import Thread
from rejson import Client, Path
from scipy.ndimage import imread
import time
import base64
import datetime


class CameraSample(Thread):
    def __init__(self, name):
        self.rj = Client(host='localhost', port=6379, decode_responses=True)
        self.jp = self.rj.pipeline()
        self.cam_name = name
        Thread.__init__(self)

    def run(self):
        startDT = datetime.datetime.now()
        img_bytes = open("samplehd.jpg", "rb").read()
        # img_metadata = {"Data": base64.b64encode(img_bytes).decode("utf-8")}
        imgs_thrown = 0
        while datetime.datetime.now() < startDT + datetime.timedelta(seconds=3):
            # self.rj.jsonset(self.cam_name, Path.rootPath(),  {"Data": base64.b64encode(img_bytes).decode("utf-8")})
            self.rj.set("{}_raw_bytes".format(self.cam_name), img_bytes)
            imgs_thrown += 1
        print("Total Images Sent: {}, {}/s".format(imgs_thrown, imgs_thrown/3.0))


class ImageReader(Thread):
    def __init__(self, name):
        self.rj = Client(host='localhost', port=6379, decode_responses=True)
        self.jp = self.rj.pipeline()
        self.cam_name = name
        Thread.__init__(self)

    def run(self):
        startDT = datetime.datetime.now()
        imgs_received = 0
        while datetime.datetime.now() < startDT + datetime.timedelta(seconds=3):
            img_encoded = self.rj.jsonget(self.cam_name, Path.rootPath())["Data"]
            img_bytes = self.rj.get("{}_raw_bytes".format(self.cam_name))
            print("Length of Decoded String: {}".format(len(img_encoded)), end="\r")
            print("Length of Image Bytse: {}")
            imgs_received += 1
        print("Total Images Received: {}, {}/s".format(imgs_received, imgs_received/3.0))


def run_tests():

    names = ["One", "Two", "Three"]
    threads = []
    for name in names:
        threads.append(CameraSample(name))
        # threads.append(ImageReader(name))

    for t in threads:
        t.start()

run_tests()