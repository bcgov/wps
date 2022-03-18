"""String representations of templates for in memory loading"""
from enum import Enum
import os

CSS_PATH = os.path.join(os.path.dirname(__file__), "style.css")


class PDFTemplateName(Enum):
    """Enumerates the possible templates client can ask for"""
    DAILY = 'daily'
    PREP = 'prep'


def get_template(template_name: str):
    """ Returns prep or daily template """
    if template_name == PDFTemplateName.DAILY.value:
        with open(os.path.join(os.path.dirname(__file__),
                               'templates/daily_template.jinja.html'),
                  'r', encoding="utf-8") as daily_template:
            return daily_template.read()
    else:
        with open(os.path.join(os.path.dirname(__file__),
                               "templates/prep_template.jinja.html"),
                  'r', encoding="utf-8") as prep_template:
            return prep_template.read()
