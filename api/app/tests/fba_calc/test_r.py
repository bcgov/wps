""" Test the we have a good version of R """
import logging
from rpy2 import robjects

logger = logging.getLogger(__name__)


def test_r_version():
    """ Test the we have a good version of R """
    response = robjects.r("version")
    # The response we get from R is pretty gross. It's a list of strings.
    # We're looking for somethin like: "['R version 4.1.2 (2021-11-01)']"
    # Would be nice to fix to a particular version, but each developers has a different
    # version of R!
    for item in response:
        # If it contains "version", it's what we're looking for.
        if 'version' in str(item):
            # Look for the version number.
            version = str(item).split(' ')[3]
            logger.info('R version: %s', version)
            # If the major version is >= 4.1.2, we're good.
            major, minor, patch = version.split('.')
            assert int(major) >= 4
            assert int(minor) >= 1
            assert int(patch) >= 2
            return
    assert False
