from functools import reduce
from itertools import groupby
from typing import List
import pdfkit
from jinja2 import Environment, FunctionLoader, Template
import json
from app.utils.pdf_data_formatter import response_2_prep_cycle_jinja_format
from app.hfi.prep_template import str_prep_template

from app.schemas.hfi_calc import (HFIResultResponse, PlanningArea,
                                  PrepCyclePDFData,
                                  StationDaily,
                                  ValidatedStationDaily)


jinja_env = Environment(loader=FunctionLoader(str_prep_template), autoescape=True)


def generate_prep_pdf(data, dates):

    rendered_output: str = ''
    template = jinja_env.get_template('prep_template')

    rendered_output += template.render(
        PlanningAreas=data,
        prepDays=dates)

    options = {
        'page-size': 'Tabloid'
    }

    pdf_bytes: bytes = pdfkit.from_string(input=rendered_output, options=options)

    return pdf_bytes
