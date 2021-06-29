""" Imports R libs, easier for mocking"""


def import_cffsdrs():
    """ Import cffdrs """
    from rpy2.robjects.packages import importr
    return importr('cffdrs')
