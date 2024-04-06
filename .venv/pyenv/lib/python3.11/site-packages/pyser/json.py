from collections import defaultdict
import json


class SchemaJSON:
    """Schema for JSON objects
    """

    def __new__(cls):
        obj = super(SchemaJSON, cls).__new__(cls)
        obj._field_dict = {}
        return obj

    def __setattr__(self, name, value):

        if type(value) is DeserField or type(value) is DeserObjectField:

            if value.name is None:
                value.name = value.name_conv(name)

            if name in self._field_dict:
                self._field_dict[name].deserialize = value
            else:
                self._field_dict[name] = CompositeField(deserialize=value)

            self.__dict__[name] = None

        elif type(value) is SerField or type(value) is SerObjectField:

            # If name is not specified use the name of the variable
            if value.name is None:
                value.name = value.name_conv(name)

            if name in self._field_dict:
                self._field_dict[name].serialize = value
            else:
                self._field_dict[name] = CompositeField(serialize=value)

            self.__dict__[name] = None

        else:
            object.__setattr__(self, name, value)

    def to_json(self, target, filename=None):
        """Serializes the object into a JSON file.
        """
        json_dict = self.to_dict(target)

        if filename is None:
            return json.dumps(json_dict)

        with open(filename, "w") as f:
            f.write(json.dumps(json_dict))

    def to_dict(self, target):
        """Converts the target into a python dict"""
        data_dict = {}
        for var_name, field in self._field_dict.items():
            serialize = field.serialize

            if target.__dict__.get(var_name, serialize.default) is None:
                if serialize.optional:
                    continue
                else:
                    print(target.__dict__)
                    raise Exception('var "{}" is None'.format(var_name))

            sub_data_dict = data_dict
            # iterate through parent keys until target key
            for key in serialize.parent_keys:
                if key in sub_data_dict:
                    if type(sub_data_dict[key]) is dict:
                        sub_data_dict = sub_data_dict[key]
                    else:
                        raise Exception(
                            ('parent key "{}" ' "is populated").format(key)
                        )
                else:
                    sub_data_dict[key] = {}
                    sub_data_dict = sub_data_dict[key]

            if type(serialize) is SerField:
                kind = serialize.kind
                if serialize.repeated:
                    sub_data_dict[serialize.name] = []
                    for value in target.__dict__.get(var_name):
                        sub_data_dict[serialize.name].append(kind(value))
                else:
                    json_value = kind(
                        target.__dict__.get(var_name, serialize.default)
                    )
                    sub_data_dict[serialize.name] = json_value
            elif type(serialize) is SerObjectField:
                if serialize.repeated:
                    sub_data_dict[serialize.name] = []
                    schema = serialize.schema()
                    for obj in target.__dict__[var_name]:
                        sub_data_dict[serialize.name].append(
                            schema.to_dict(obj))
                else:
                    obj = target.__dict__[var_name]
                    schema = serialize.schema()
                    sub_data_dict[serialize.name] = schema.to_dict(obj)

        return data_dict

    def from_json(self, target, filename=None, raw_json=None):
        """Loads in values to this object from a JSON file or string"""
        if filename is not None:
            with open(filename, "r") as f:
                raw_json = f.read()
        elif raw_json is None:
            raise Exception("Specify filename or raw JSON")

        data_dict = json.loads(raw_json)
        return self.from_dict(target, data_dict)

    def from_dict(self, target, data_dict):
        """Loads in values to this object from a python dict"""
        for var_name, field in self._field_dict.items():
            deserialize = field.deserialize
            sub_data_dict = data_dict

            for key in deserialize.parent_keys:
                if key in sub_data_dict:
                    sub_data_dict = sub_data_dict[key]
                elif deserialize.optional:
                    continue
                else:
                    raise Exception(
                        (
                            'parent_key "{}" does not exists for ' "field {}"
                        ).format(key, deserialize.name)
                    )

            if deserialize.name not in sub_data_dict:
                if deserialize.optional:
                    continue
                raise Exception(
                    "{} field not found in the json".format(deserialize.name)
                )

            if type(deserialize) is DeserField:
                if deserialize.repeated:
                    target.__dict__[var_name] = []
                    for value in sub_data_dict[deserialize.name]:
                        target.__dict__[var_name].append(deserialize.kind(value))
                else:
                    target.__dict__[var_name] = deserialize.kind(
                        sub_data_dict[deserialize.name]
                    )
            elif type(deserialize) is DeserObjectField:
                if deserialize.repeated:
                    target.__dict__[var_name] = []
                    for value in sub_data_dict[deserialize.name]:
                        schema = deserialize.schema()
                        obj = deserialize.kind()
                        schema.from_dict(obj, value)
                        target.__dict__[var_name].append(obj)
                else:
                    obj = deserialize.kind()
                    schema = deserialize.schema()
                    schema.from_dict(obj, sub_data_dict[deserialize.name])
                    target.__dict__[var_name] = obj
        return target


class CompositeField:
    """Class for holding both serialize and deserialize fields"""

    def __init__(self, serialize=None, deserialize=None):
        self.serialize = serialize
        self.deserialize = deserialize


class Field:
    """Super class for fields"""

    def __str__(self):
        return "(name: {0}, kind: {1})".format(self.name, self.kind)

    __repr__ = __str__


class DeserField(Field):
    """DeserField
    name:
        name of the field that should be deserialized from, default is the
        name of the variable
    kind:
        the type of the variable should be deserialized to, default is what
        the deserialized variable is
    optional:
        specifies if the value is optional, if value is not found as a field
        the variable is left as None
    parent_keys
        The parent keys of this field.
    """

    def __init__(
        self,
        name=None,
        name_conv=lambda x: x,
        kind=lambda x: x,
        optional=False,
        repeated=False,
        parent_keys=[],
    ):
        self.name = name
        self.name_conv = name_conv
        self.kind = kind
        self.optional = optional
        self.repeated = repeated
        self.parent_keys = parent_keys

        if not callable(kind):
            raise Exception("Kind needs to be callable")


class SerField(Field):
    """SerField
    name:
        name of the field that should serialize to, defaults to the variable
        name
    kind:
        the type that the field should be serialized to, defaults to the type
        that the variable is
    optional:
        specifies if the value is optional, if value is None then it will not
        get serialized
    parent_keys
        The parent keys of this field.
    default
        The default value of this field. Field must be optional to have
        default value.
    """

    def __init__(
        self,
        name=None,
        name_conv=lambda x: x,
        kind=lambda x: x,
        optional=False,
        repeated=False,
        parent_keys=[],
        default=None,
    ):
        self.name = name
        self.name_conv = name_conv
        self.kind = kind
        self.optional = optional
        self.repeated = repeated
        self.parent_keys = parent_keys
        self.default = default

        if not callable(kind):
            raise Exception("Kind needs to be callable")


class ObjectField:
    """Super class for object fields"""

    def __str__(self):
        return "(name: {0}, repeated: {1})".format(self.name, self.repeated)

    __repr__ = __str__


class SerObjectField(ObjectField):
    """SerObjectField
    name:
        name of the field that should serialize to, defaults to the variable
        name
    kind:
        the type that the field should be serialized to, defaults to the type
        that the variable is
    optional:
        specifies if the value is optional, if value is None then it will not
        get serialized
    parent_keys
        The parent keys of this field.

    """

    def __init__(
        self,
        name=None,
        name_conv=lambda x: x,
        optional=False,
        repeated=False,
        parent_keys=[],
        default=None,
        schema=None
    ):
        if schema is None:
            raise Exception("Schema cannot be None")

        if not optional and default is not None:
            raise Exception("Default value populated while optional")

        if not type(parent_keys) is list:
            raise Exception("parent keys has to be of type list")

        self.name = name
        self.name_conv = name_conv
        self.optional = optional
        self.repeated = repeated
        self.parent_keys = parent_keys
        self.default = default
        self.schema = schema


class DeserObjectField(ObjectField):
    """DeserObjectField

    name
        The name of the field that should contain this object.
    optional
        Specifies if this field is optional.
    repeated
        Specifies if this field contains a list.
    kind
        Specifies which class should be instantiated for this field.
    parent_keys
        The parent keys of this field.
    """

    def __init__(
        self,
        name=None,
        name_conv=lambda x: x,
        optional=False,
        repeated=False,
        kind=None,
        schema=None,
        parent_keys=[],
    ):

        if schema is None:
            raise Exception("Schema cannot be None")

        self.name = name
        self.name_conv = name_conv
        self.optional = optional
        self.repeated = repeated
        self.kind = kind
        self.parent_keys = parent_keys
        self.schema = schema
