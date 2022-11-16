""" Test the we have a good version of R """
import logging
from packaging import version
from rpy2 import robjects

logger = logging.getLogger(__name__)


def test_r_version():
    """ Test the we have a good version of R """
    response = robjects.r("version")
    # The response we get from R is pretty gross. It's a list of strings.
    # We're looking for somethin like: "['R version 4fb .1.2 (2021-11-01)']"
    # Would be nice to fix to a particular version, but each developers has a different
    # version of R!
    for item in response:
        # If it contains "version", it's what we're looking for.
        if 'version' in str(item):
            # Look for the version number.
            r_version = str(item).split(' ')[3]
            logger.info('R version: %s', r_version)
            # If the major version is >= 4.1.2, we're good.
            assert version.parse(r_version) >= version.parse('4.1.2')
            return
    assert False
