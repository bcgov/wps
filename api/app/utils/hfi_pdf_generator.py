from reportlab.platypus import SimpleDocTemplate
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Table
import io

fileName = io.BytesIO()
data = [
    ['Fraser (V1)', '1.3', '0-1', '1'],
    ['Honna (93)', '21', 'C5', '0.0', '2.6', '1']
]

pdf = SimpleDocTemplate(fileName,
                        pagesize=letter)

table = Table(data)
elems = []
elems.append(table)
pdf.build(elems)
f = open('pdfTest.pdf', 'b+w')
fileName.seek(0)
f.write(fileName.read())
