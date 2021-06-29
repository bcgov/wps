""" Imports R libs, easier for mocking"""
from rpy2.robjects.packages import importr


def import_cffsdrs():
    """ Import cffdrs """
    return importr('cffdrs')
