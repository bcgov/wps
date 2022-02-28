import pdfkit
from jinja2 import Template

daily_template_path = "api/app/utils/rendered_daily_template.html"
output_file_path = "api/app/utils/out.pdf"


def generate_daily_pdf():
    with open(daily_template_path, 'r') as daily_template:
        template = Template(daily_template.read())
        template.render()

    options = {
        'page-size': 'Tabloid'
    }

    return pdfkit.from_file(daily_template_path,
                            output_file_path, options)
