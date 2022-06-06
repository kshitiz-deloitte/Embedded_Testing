import os
import configparser


def read_config(cfg_file):
    if cfg_file is not None:
        config1 = configparser.RawConfigParser()
        if os.path.exists(cfg_file):
            config1.read(cfg_file)
        return config1


config = read_config(r'Test/resources/app.properties')


def get_from_config(field):
    return config.get(field)
