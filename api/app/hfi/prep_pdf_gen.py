"""Generate a prep cycle PDF"""
import pdfkit
from jinja2 import Environment, FunctionLoader
from app.hfi.prep_template import CSS_PATH, str_prep_template


jinja_env = Environment(loader=FunctionLoader(str_prep_template), autoescape=True)


def generate_prep_pdf(data, dates):
    """Generate a prep PDF"""

    rendered_output: str = ''
    template = jinja_env.get_template('prep_template')

    rendered_output += template.render(
        PlanningAreas=data,
        prepDays=dates)

    options = {
        'page-size': 'Tabloid'
    }

    pdf_bytes: bytes = pdfkit.from_string(input=rendered_output, options=options, css=CSS_PATH)

    return pdf_bytes
