import pdfkit
from jinja2 import Template

from app.schemas.hfi_calc import HFIResultResponse
from app.utils.pdf_data_formatter import response_2_daily_jinja_format

daily_template_path = "api/app/utils/daily_template.html"
daily_rendered_path = "api/app/utils/daily_rendered.html"

output_file_path = "api/app/utils/out.pdf"


def generate_daily_pdf(result: HFIResultResponse):
    with open(daily_template_path, 'r') as daily_template:
        template = Template(daily_template.read())
        with open(daily_rendered_path, 'w') as new_page:
            daily_pdf_data_by_date = response_2_daily_jinja_format(result)
            for date_key, planning_area_data in daily_pdf_data_by_date.items():
                new_page.write(template.render(
                    date=date_key,
                    daily_data=planning_area_data,
                    daily_pdf_data_by_date=daily_pdf_data_by_date,
                    fire_centre_id=result.selected_fire_center_id))

    options = {
        'page-size': 'Tabloid'
    }

    return pdfkit.from_file(daily_rendered_path,
                            output_file_path, options)
