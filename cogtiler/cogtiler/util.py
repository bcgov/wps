import numpy as np


def lookup(value):
    """ Take an HFI value as input, and output an RGBA tuple
    0-10        : 0100fc
    10-500      : 0481ff
    500-2000    : 057c04
    2000-4000   : 03fe03
    4000-10000  : feff04
    10000-30000 : f9ab03
    30000+      : fd0100
    """
    if value < 0:
        return 0, 0, 0, 0
    if value >= 0 and value < 10:
        return 0x01, 0x00, 0xfc, 0xff
    elif value >= 10 and value < 500:
        return 0x04, 0x81, 0xff, 0xff
    elif value >= 500 and value < 2000:
        return 0x05, 0x7c, 0x04, 0xff
    elif value >= 2000 and value < 4000:
        return 0x03, 0xfe, 0x03, 0xff
    elif value >= 4000 and value < 10000:
        return 0xfe, 0xff, 0x04, 0xff
    elif value >= 10000 and value < 30000:
        return 0xf9, 0xab, 0x03, 0xff
    elif value >= 30000:
        return 0xfd, 0x01, 0x00, 0xff


def classify(data):
    """
    Given a numpy array, with a single band, classify the values into RGB and mask tuples.

    NOTE: This is probably a very slow way of doing it - there shouldn't be a way of doing
    this without enumerating. I'm just not a numpy expert.
    """
    r, g, b = 0, 1, 2
    rgb = np.empty((3, data.shape[1], data.shape[2]), np.uint8)
    mask = np.empty(data.shape[1:], np.uint8)
    for band in data:
        for y, row in enumerate(band):
            for x, col in enumerate(row):
                rgb[r][y][x], rgb[g][y][x], rgb[b][y][x], mask[y][x] = lookup(col)
    return rgb, mask
