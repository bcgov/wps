import sys
from csv import reader

with open('C-7.csv') as c7:
    csv_reader = reader(c7)
    header = next(csv_reader)

    output = sys.stdout

    output.write('const c7 = [')
    for row in reader(c7):
        first = True
        output.write('[')
        for col in row[1:]:
            if not first:
                output.write(',')
            else:
                first = False
            output.write(col)
        output.write('],')
        output.write('\n')
    output.write(']\n')
