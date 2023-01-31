import configparser
import pathlib

import pytest

from ..transforms import *  # Module under test
from ..contexts import local_context


TEST_DIR = pathlib.Path(__file__).parent.absolute()
DATA_DIR = TEST_DIR / "data"


@pytest.fixture(scope="session")
def config():
    config = configparser.ConfigParser()
    config.read(f"{DATA_DIR}/settings.ini", encoding="utf-8")
    return config


def test_config_file(config):
    assert config["DEV"]["host"] == "localhost"


def test_context_from_config(config):
    with local_context(config):
        assert resolve("[DEV.HOST]") == "localhost"
