from remi import datatypes


def metadata_listener():
    listener = datatypes.MetadataListener()
    listener.start()
    listener.join()

metadata_listener()