from mimetypes import init
import pdfkit
from jinja2 import Template
import json

json_file = open('/Users/jforeman/Workspace/wps/api/app/utils/test_json.json')
html = open('/Users/jforeman/Workspace/wps/api/app/templates/template1.html').read()

data = json.load(json_file)
template = Template(html)


class PrepCyclePdfResponse:
    def __init__(self, planningAreaName, elev, fuelType, grassCure, dailies):
        self.planningAreaName = planningAreaName
        self.elev = elev
        self.fuelType = fuelType
        self.grassCure = grassCure
        self.dailies = dailies  # dailies is the stations grouped by station code containing the dailies for each day in the prep cycle


with open('/Users/jforeman/Workspace/wps/api/app/utils/rendered_template.html', 'w') as new_page:
    new_page.write(template.render(planningAreas=data['planning_area_hfi_results']))


options = {
    'page-size': 'Tabloid'
}

pdfkit.from_file('/Users/jforeman/Workspace/wps/api/app/utils/rendered_template.html',
                 '/Users/jforeman/Workspace/wps/api/app/utils/out.pdf', options)
