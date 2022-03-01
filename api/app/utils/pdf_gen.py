from functools import reduce
from itertools import groupby
from typing import List
import pdfkit
from jinja2 import Template
import json

from app.schemas.hfi_calc import (HFIResultResponse,
                                  PrepCyclePDFData,
                                  StationDaily,
                                  ValidatedStationDaily)

json_file = open('/Users/jforeman/Workspace/wps/api/app/utils/test_json.json')
html = open('/Users/jforeman/Workspace/wps/api/app/templates/template1.html').read()

data = json.load(json_file)
template = Template(html)

with open('/Users/jforeman/Workspace/wps/api/app/utils/rendered_template.html', 'w') as new_page:
    new_page.write(template.render(planningAreas=data['planning_area_hfi_results']))


options = {
    'page-size': 'Tabloid'
}

pdfkit.from_file('/Users/jforeman/Workspace/wps/api/app/utils/rendered_template.html',
                 '/Users/jforeman/Workspace/wps/api/app/utils/out.pdf', options)
