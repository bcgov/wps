import pdfkit
from jinja2 import Template

from app.schemas.hfi_calc import HFIResultResponse

daily_template_path = "api/app/utils/daily_template.html"
daily_rendered_path = "api/app/utils/daily_rendered.html"

output_file_path = "api/app/utils/out.pdf"


def generate_daily_pdf(result: HFIResultResponse):
    with open(daily_template_path, 'r') as daily_template:
        template = Template(daily_template.read())
        with open(daily_rendered_path, 'w') as new_page:
            jinja_data = result_to_dicts(result)

            new_page.write(template.render(date='01-01-2022',
                           fire_centre_id=result.selected_fire_center_id))

    options = {
        'page-size': 'Tabloid'
    }

    return pdfkit.from_file(daily_rendered_path,
                            output_file_path, options)


def result_to_dicts(result: HFIResultResponse):
    jinja_dicts = []
    for planning_area in result.planning_area_hfi_results:
        pl = {'planning_area': planning_area.__dict__}
        for daily_result in planning_area.daily_results:
            pl['date'] = daily_result.dateISO
            pl['dailies'] = list(map(lambda x: x.daily.__dict__, daily_result.dailies))

    jinja_dicts.append(pl)
