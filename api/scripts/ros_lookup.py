import json
# https://rpy2.github.io/doc/latest/html/introduction.html#r-packages
from rpy2.robjects.packages import importr


cffrds = importr('cffdrs')

fuel_types = ("C1", "C2", "C3", "C4", "C5", "C6", "C7", "D1", "M1", "M2", "M3", "M4",
         "S1", "S2", "S3", "O1A", "O1B")

data = {}


def get_m1_row(fuel_type, isi, bui, pcs):
    m_row = []
    for pc in pcs:
        # TODO: validate SFC!
        ros = cffrds._ROScalc(FUELTYPE=fuel_type, ISI=isi, BUI=bui, CBH=6, SFC=1.5, PC=pc)
        m_row.append(round(ros[0]))
    return m_row


def get_m3_row(fuel_type, isi, bui, pdfs):
    m_row = []
    for pdf in pdfs:
        # TODO: validate SFC
        ros = cffrds._ROScalc(FUELTYPE=fuel_type, ISI=isi, BUI=bui, CBH=6, SFC=1.5, PDF=pdf)
        m_row.append(round(ros[0]))
    return m_row
    

for fuel_type in fuel_types:
    print(fuel_type)
    ft_data = data[fuel_type] = []
    for isi in range(1, 70):
        isi_row = []
        ft_data.append(isi_row)
        for bui in range(0, 200):
            if fuel_type == "C6":
                cbh_row = []
                isi_row.append(cbh_row)
                for cbh in (7, 2):
                    # FMC - foliar moisture content, redbook has 97%
                    # CBH - crown to base height, redbook has 7 and 2
                    # SFC - Surface Fuel Consumption (kg/m^2) - ???? NO IDEA!
                    # TODO: validate SFC
                    ros = cffrds._ROScalc(FUELTYPE=fuel_type, ISI=isi, BUI=bui, FMC=97, CBH=cbh, SFC=1, PC=100)
                    cbh_row.append(round(ros[0]))
            elif fuel_type == "M1" or fuel_type == "M2":
                isi_row.append(get_m1_row(fuel_type, isi, bui, pcs=(75, 50, 25)))
            elif fuel_type == "M3" or fuel_type == "M4":
                isi_row.append(get_m3_row(fuel_type, isi, bui, pdfs=(30, 60, 100)))
            elif fuel_type == "O1A" or fuel_type == "O1B":
                ros = cffrds._ROScalc(FUELTYPE=fuel_type, ISI=isi, BUI=bui, CC=bui)
                isi_row.append(round(ros[0]))
            else:
                ros = cffrds._ROScalc(FUELTYPE=fuel_type, ISI=isi, BUI=bui)
                isi_row.append(round(ros[0]))
print('write file...')
with open(f'ros_lookup.json', 'w') as f:
    json.dump(data, f)
print('done.')