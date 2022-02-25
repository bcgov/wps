
import xlsxwriter
import pandas as pd
import pdfkit as pdf
from app.schemas.hfi_calc import HFIResultRequest, HFIResultResponse

file_prefix = 'xlsxwriter-sample'
xlsx_file_name = file_prefix + '.xlsx'
html_file_name = file_prefix + '.html'
pdf_file_name = file_prefix + '.pdf'

prep_sheet_name = "Prep Period"


def generate_pdf(result: HFIResultRequest):
    """ Generates PDF based on calculated HFI result"""
    workbook = xlsxwriter.Workbook(xlsx_file_name)

    # Add prep week sheet
    ws = workbook.add_worksheet(prep_sheet_name)

    planning_areas = build_planning_areas(result)

    daily_column_headers = build_headers(result)

    data = [
        [''] + ['Monday', "Tuesday", "Wednesday", "Thursday", "Friday"],
        ['Planning Area/Station', "Elev.", "Fuel Type", "Grass Cure"],
        ['Fraser Zone'],
        ['Apples'] + [10000, 5000, 8000, 6000],
        ['Pears'] + [2000, 3000, 4000, 5000],
        ['Bananas'] + [6000, 6000, 6500, 6000],
        ['Oranges'] + [500, 300, 200, 700]
    ]

    # Add prep week data from calculated hfi result
    ws.add_table(0, 0, 8, 8, {'data': data})

    # Save and close
    workbook.close()

    # Create the spreadsheet
    xl = pd.ExcelFile(xlsx_file_name)

    # parse sheet into dataframe
    df = xl.parse(prep_sheet_name)

    # output to html to generate pdf
    df.to_html(html_file_name, index=False, na_rep='', index_names=False, header=False, border=1)

    # generate pdf
    pdf.from_file(html_file_name, pdf_file_name)


def build_planning_areas(result: HFIResultResponse):
    return []


def build_headers(result: HFIResultResponse):
    """ Build headers for the spreadsheet """
    date_headers = []
    for area_result in result.planning_area_hfi_results:
        for daily_result in area_result.daily_results:
            date_headers.append(daily_result.dateISO)
    return date_headers
