from reportlab.platypus import Table
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

fileName = io.BytesIO()
prepPeriod = [
    ['Fraser (V1)', '1.3', '0-1', '1'],
    ['Honna (93)', '21', 'C5', '0.0', '2.6', '1']
]

pdf = canvas.Canvas('pdfTest.pdf', pagesize=A4)

width, height = A4

prepPeriodHeightList = [
    height * 10 / 100,
    height * 90 / 100
]
prepPeriodWidthList = [
    width * 10 / 100,
    width * 80 / 100,
    width * 10 / 100
]
prepPeriodTable = Table(['spacer', 'content', 'spacer'],
                        ['spacer', 'content', 'spacer'],
                        wolWidths=prepPeriodWidthList,
                        colHeights=prepPeriodHeightList)

prepPeriodTable.setStyle([
    ('GRID', (0, 0), (-1, -1), 1, 'red')
])
prepPeriodTable.wrapOn(pdf, 0, 0)
prepPeriodTable.drawOn(pdf, 0, 0)

elems = []
elems.append(prepPeriodTable)
pdf.save(elems)
f = open('pdfTest.pdf', 'b+w')
fileName.seek(0)
f.write(fileName.read())
