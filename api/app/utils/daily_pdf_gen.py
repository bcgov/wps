import pdfkit
from jinja2 import Template


def generate_daily_pdf():
    html = open('api/app/templates/template1.html').read()

    template = Template(html)

    with open('api/app/utils/rendered_template.html', 'w') as new_page:
        new_page.write(template.render())

    options = {
        'page-size': 'Tabloid'
    }

    return pdfkit.from_file('api/app/utils/rendered_daily_template.html',
                            'api/app/utils/out2.pdf', options)
