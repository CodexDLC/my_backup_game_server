import logging
import sys
import colorlog
from logging.handlers import RotatingFileHandler

handler = logging.StreamHandler(sys.stdout)
formatter = formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")


def get_console_handler(level):
    formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(levelname)-8s%(reset)s | %(blue)s%(message)s",
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bold_red'
        }
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(formatter)
    return handler

def get_file_handler(path, level, max_size, backups):
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler = RotatingFileHandler(path, maxBytes=max_size, backupCount=backups)
    handler.setLevel(level)
    handler.setFormatter(formatter)
    return handler
