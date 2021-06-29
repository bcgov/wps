""" Imports R libs, easier for mocking"""


def import_cffsdrs():
    """ Import cffdrs """
    # pylint: disable= import-outside-toplevel
    from rpy2.robjects.packages import importr
    return importr('cffdrs')
