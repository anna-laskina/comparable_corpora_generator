import json
import os

import numpy as np


def save_data(data, filename, data_type='json'):
    """Function to save files.

    :param data: data
    :param filename: path to save data.
    :param data_type: type of data (def. 'json').
    :return: None
    """
    if data_type == 'json':
        with open(filename, 'w') as f:
            json.dump(data, f)
    elif data_type == 'np':
        np.save(filename, data)


def read_data(filename, data_type='json'):
    """Function to loading data from a file.

    :param filename: path to the file.
    :param data_type: type of data (def. 'json').
    :return: data
    """
    if data_type == 'json':
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            dirpath = os.path.dirname(__file__)
            filepath = os.path.join(dirpath, filename)
            with open(filepath, 'r') as f:
                return json.load(f)
    elif data_type == 'np':
        return np.load(filename)


def path_check(path, if_create=True):
    """

    :param path: str, the path to be checked
    :param if_create: Bool, If true, a [path] directory will be created
    :return: None
    """
    if path is not None and not os.path.exists(path):
        print(f'path: {path} dosn\'t exist')
        if if_create:
            os.makedirs(path)
            print(f"The directory {path} is created!")


def sec2hms(time):
    h = int(time // 3600)
    m = int((time % 3600) // 60)
    s = int(time % 60)
    return f'{h:d}:{m:02d}:{s:02d}'


def remove_elements_from_list(main_list, remove_list):
    """ Function to remove elements from a list.
    :param main_list: source list to remove elements from
    :param remove_list: list that contains the deleted elements
    :return: list without remove elements
    """
    return_list = main_list[:]
    for remove_element in remove_list:
        if remove_element in return_list:
            return_list.remove(remove_element)
    return return_list
