import pdfkit
from jinja2 import Template

daily_template_path = "api/app/utils/daily_template.html"
daily_rendered_path = "api/app/utils/daily_rendered.html"

output_file_path = "api/app/utils/out.pdf"


def generate_daily_pdf():
    with open(daily_template_path, 'r') as daily_template:
        template = Template(daily_template.read())
        with open(daily_rendered_path, 'w') as new_page:
            new_page.write(template.render(date='01-01-2022'))

    options = {
        'page-size': 'Tabloid'
    }

    return pdfkit.from_file(daily_rendered_path,
                            output_file_path, options)
