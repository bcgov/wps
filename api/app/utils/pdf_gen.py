from functools import reduce
from itertools import groupby
from typing import List
import pdfkit
from jinja2 import Template
import json
from app.utils.pdf_data_formatter import response_2_prep_cycle_jinja_format

from app.schemas.hfi_calc import (HFIResultResponse,
                                  PrepCyclePDFData,
                                  StationDaily,
                                  ValidatedStationDaily)


def generate_prep_pdf(data):

    html = open('/Users/jforeman/Workspace/wps/api/app/templates/template1.html').read()

    template = Template(html)

    with open('/Users/jforeman/Workspace/wps/api/app/utils/rendered_template.html', 'w') as new_page:
        new_page.write(template.render(planningAreas=data))

        options = {
            'page-size': 'Tabloid'
        }

    pdfkit.from_file('/Users/jforeman/Workspace/wps/api/app/utils/rendered_template.html',
                     '/Users/jforeman/Workspace/wps/api/app/utils/out.pdf', options)
