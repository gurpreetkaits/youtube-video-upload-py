import configparser


class ConfigBaseParent(object):
    # TODO: add checks for if filename is valid
    def to_config(self, filename=None):
        config = configparser.ConfigParser()

        for field_name, field in self._config_key_dict.items():
            serialize = field.serialize
            if serialize is None:
                continue

            value = self.__dict__[field_name]
            if value is None and serialize.optional:
                continue

            value = serialize.kind(value)

            if not config.has_section(serialize.section):
                config.add_section(serialize.section)
            config.set(serialize.section, serialize.name, value)

        if filename is not None:
            with open(filename, "w") as f:
                config.write(f)
        else:
            return config

    def from_config(self, filename):
        config = configparser.ConfigParser()
        config.read(filename)
        for field_name, field in self._config_key_dict.items():
            deserialize = field.deserialize
            if deserialize is None:
                continue

            if type(field) is CompositeConfigOption:
                if config.has_option(deserialize.section, deserialize.name):
                    self.__dict__[field_name] = field.deserialize.kind(
                        config.get(deserialize.section, deserialize.name)
                    )
                elif (
                    not config.has_section(deserialize.section)
                    and not deserialize.optional
                ):
                    raise Exception(
                        '"{}" section not in config'.format(deserialize.section)
                    )
                elif not deserialize.optional:
                    raise Exception(
                        '"{}" option not in config'.format(deserialize.name)
                    )
            elif type(field) is CompositeConfigSection:
                self.__dict__[field_name].from_config(filename)


class ConfigSectionBase(ConfigBaseParent):
    """ConfigSectionBase
    """

    def __new__(cls):
        obj = super(ConfigSectionBase, cls).__new__(cls)
        obj._config_key_dict = {}
        return obj

    def __setattr__(self, name, value):
        if type(value) is DeserConfigOption:
            if value.name is None:
                value.name = name

            if name in self._config_key_dict:
                self._config_key_dict[name].deserialize = value
            else:
                self._config_key_dict[name] = CompositeConfigOption(
                    deserialize=value
                )
            self.__dict__[name] = None

        elif type(value) is SerConfigOption:
            if value.name is None:
                value.name = name

            if name in self._config_key_dict:
                self._config_key_dict[name].serialize = value
            else:
                self._config_key_dict[name] = CompositeConfigOption(
                    serialize=value
                )
            self.__dict__[name] = None
        else:
            object.__setattr__(self, name, value)

    def __set_serialize_section__(self, section):
        for field in self._config_key_dict.values():
            if field.serialize is not None:
                field.serialize.section = section

    def __set_deserialize_section__(self, section):
        for field in self._config_key_dict.values():
            if field.deserialize is not None:
                field.deserialize.section = section


class ConfigBase(ConfigBaseParent):
    def __new__(cls):
        obj = super(ConfigBase, cls).__new__(cls)
        obj._config_key_dict = {}
        return obj

    def __setattr__(self, name, value):
        if type(value) is DeserConfigOption:
            if value.name is None:
                value.name = name
            if name in self._config_key_dict:
                self._config_key_dict[name].deserialize = value
            else:
                self._config_key_dict[name] = CompositeConfigOption(
                    deserialize=value
                )
            self.__dict__[name] = None
        elif type(value) is DeserConfigSection:
            obj = value.kind()
            obj.__set_deserialize_section__(value.section)
            if name in self._config_key_dict:
                self._config_key_dict[name].deserialize = value
            else:
                self._config_key_dict[name] = CompositeConfigSection(
                    deserialize=value
                )
            self.__dict__[name] = obj

        elif type(value) is SerConfigOption:
            if value.name is None:
                value.name = name

            if name in self._config_key_dict:
                self._config_key_dict[name].serialize = value
            else:
                self._config_key_dict[name] = CompositeConfigOption(
                    serialize=value
                )
            self.__dict__[name] = None

        elif type(value) is SerConfigSection:
            obj = value.kind()
            obj.__set_serialize_section__(value.section)
            if name in self._config_key_dict:
                self._config_key_dict[name].serialize = value
            else:
                self._config_key_dict[name] = CompositeConfigSection(
                    serialize=value
                )
            self.__dict__[name] = obj
        else:
            object.__setattr__(self, name, value)


class CompositeConfigOption:
    def __init__(self, serialize=None, deserialize=None, is_section=False):
        self.serialize = serialize
        self.deserialize = deserialize

    def __str__(self):
        return "serialize: {} deserialize: {}".format(
            self.serialize, self.deserialize
        )

    __repr__ = __str__


class ConfigOption:
    def __str__(self):
        return "(section {0} name: {1}, kind: {2}, optional: {3})".format(
            self.section, self.name, self.kind, self.optional
        )

    __repr__ = __str__


class SerConfigOption(ConfigOption):
    def __init__(self, name=None, section=None, kind=str, optional=False):
        self.name = name
        self.section = section
        self.kind = kind
        self.optional = optional


class DeserConfigOption(ConfigOption):
    def __init__(
        self, name=None, section=None, kind=lambda x: x, optional=False
    ):
        self.name = name
        self.section = section
        self.kind = kind
        self.optional = optional


class CompositeConfigSection:
    def __init__(self, serialize=None, deserialize=None, is_section=False):
        self.serialize = serialize
        self.deserialize = deserialize

    def __str__(self):
        return "serialize: {} deserialize: {}".format(
            self.serialize, self.deserialize
        )

    __repr__ = __str__


class ConfigSection:
    def __str__(self):
        return "(section {0} optional: {1})".format(self.section, self.optional)

    __repr__ = __str__


class SerConfigSection(ConfigSection):
    def __init__(self, kind, section, optional=False):
        self.kind = kind
        self.section = section
        self.optional = optional


class DeserConfigSection(ConfigSection):
    def __init__(self, kind, section, optional=False):
        self.kind = kind
        self.section = section
        self.optional = optional
