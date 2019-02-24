from abc import ABC, abstractmethod


class SpecialCaseHandler(ABC):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def check_fit(self, value):
        """
        Check if the value is such that this is the class that ought to handle storing and loading it
        :param value:
        :return:
        """
        pass

    @abstractmethod
    def write(self, key, value, client):
        """
        Given a top level key name and a value, write to the redis database however you choose
        :param key: Top Key to store value under in redis
        :param value: Data to store
        :param client: Client to use
        :return: None
        """
        pass

    @abstractmethod
    def read(self, key, value, client):
        """
        Given a top level key name and a value, write to the redis database however you choose
        :param key: Top Key under which the encoded value is stored
        :param client: Client to use
        :return: Decoded redis db entry
        """
        pass

    @abstractmethod
    def get_identifier(self):
        """
        Return a string that will be used in key names to indicate this class should be used to decode data
        """
        pass
