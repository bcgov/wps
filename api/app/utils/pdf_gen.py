import pdfkit
from jinja2 import Template

html = open('/Users/jforeman/Workspace/wps/api/app/templates/template1.html').read()

template = Template(html)

with open('/Users/jforeman/Workspace/wps/api/app/utils/rendered_template.html', 'w') as new_page:
    new_page.write(template.render())

options = {
    'page-size': 'Tabloid'
}

pdfkit.from_file('/Users/jforeman/Workspace/wps/api/app/utils/rendered_template.html',
                 '/Users/jforeman/Workspace/wps/api/app/utils/out.pdf', options)
