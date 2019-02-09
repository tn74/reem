class SynchroDict(dict):
    def __init__(self, *args, **kwargs):

        # Ensure that this dictionary knows what it's key in its parent dictionary is
        if 'super_key' not in kwargs.keys():
            raise KeyError("No key name for initialization of SynchroDict")
        self.super_key = kwargs['super_key']

        # Ensure that this dictionary has access to it's parent dictionary
        self.parent_dictionary = None
        if 'parent_dictionary' in kwargs.keys():
            if type(kwargs['parent_dictionary']) is not type(self):
                raise ValueError("Parent Dictionary is not of type SynchroDict")
            self.parent_dictionary = kwargs['parent_dictionary']

        # Map value types to their set handlers
        self.set_handlers = {
            str: self.handle_set_string,
            dict: self.handle_set_dict
        }

        # Initialize like a dictionary is supposed to
        super(SynchroDict, self).__init__(*args, **kwargs)

    def get_redis_base_key(self):
        if self.parent_dictionary is not None:
            return "{}.{}".format(self.parent_dictionary.get_redis_base_key(), self.super_key)
        else:
            return self.super_key

    def __setitem__(self, item, value):
        if type(value) not in self.set_handlers.keys():
            raise ValueError("Value of Type {} not currently accepted".format(type(value)))
        self.set_handlers[type(value)](item, value)

    def handle_set_string(self, item, value):
        super(SynchroDict, self).__setitem__(item, value)

    def handle_set_dict(self, item, value):
        synchro_equivalent = SynchroDict(super_key=item, parent_dictionary=self)
        for k, v in value.items():
            synchro_equivalent[k] = v
        super(SynchroDict, self).__setitem__(item, synchro_equivalent)
