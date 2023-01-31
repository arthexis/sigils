import pytest
from dataclasses import dataclass

from ..transforms import *  # Module under test
from ..errors import SigilError
from ..contexts import local_context

DATABASE = []


class Manager:

    @staticmethod
    def get(**kwargs):
        for obj in DATABASE:
            current = None
            for key, val in kwargs.items():
                if getattr(obj, key) == val:
                    current = obj
                else:
                    current = None
            if current:
                return current

    def get_by_natural_key(self, name):
        return self.get(name=name)


class Model:
    """Simulate a Django ORM model."""

    def save(self):
        DATABASE.append(self)

    objects = Manager()


@dataclass
class UserModel(Model):
    pk: int
    name: str
    alias: str


def test_model_has_objects_attribute():
    assert hasattr(UserModel, "objects")


def test_model_context_class():
    UserModel(pk=1, name="arthexis", alias="admin").save()
    with local_context(USR=UserModel):
        assert resolve("[USR]", serializer=lambda x: x.__name__) == "UserModel"


def test_model_context_pk_attribute():
    UserModel(pk=1, name="arthexis", alias="admin").save()
    with local_context(USR=UserModel):
        assert resolve("[USR=1.NAME]") == "arthexis"


def test_model_context_pk():
    UserModel(pk=2, name="arthexis", alias="admin").save()
    with local_context(USR=UserModel):
        assert resolve("[USR.NAME='arthexis'.PK]") == "1"


def test_model_context_wrong_attribute():
    UserModel(pk=3, name="arthexis", alias="admin").save()
    with local_context(USR=UserModel):
        with pytest.raises(SigilError):
            assert resolve("[USR='admin'.NAME]", on_error=OnError.RAISE)


def test_model_context_get_by_natural_key():
    UserModel(pk=3, name="arthexis", alias="admin").save()
    with local_context(USR=UserModel):
        assert resolve("[USR='arthexis'.ALIAS]") == 'admin'


# Test serializing a model using json from the standard library
def test_model_json_serialization():
    import json
    UserModel(pk=3, name="arthexis", alias="admin").save()
    with local_context(USR=UserModel):
        assert json.loads(resolve("[USR='arthexis'.ALIAS]", serializer=json.dumps)) == 'admin'

