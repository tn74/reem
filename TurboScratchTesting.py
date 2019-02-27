import TurboDT, TurboHandlers
import numpy as np


def metadata_listener():
    listener = TurboDT.MetadataListener()
    listener.start()
    listener.join()

metadata_listener()