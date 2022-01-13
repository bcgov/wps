from math import pi
import json
import os
import random
import rpy2.robjects as robjs
from rpy2.robjects import DataFrame
from rpy2.robjects.packages import importr
import rpy2.robjects.conversion as cv
from rpy2.rinterface import NULL


def _none2null(_):
    """Turn None values into null"""
    return robjs.r("NULL")


none_converter = cv.Converter("None converter")
none_converter.py2rpy.register(type(None), _none2null)


def random_fmc():
    if random.getrandbits(1) == 0:
        return 0.0
    else:
        return random.uniform(0, 100)


def generate_input_data() -> dict:
    fuel_types = [
        "C1",
        "C2",
        "C3",
        "C4",
        "C5",
        "C6",
        "C7",
        "D1",
        "M1",
        "M2",
        "M3",
        "M4",
        "S1",
        "S2",
        "S3",
        "O1A",
        "O1B",
    ]
    data = []
    # seed with meaning of life, for consistency.
    random.seed(42)
    # for each fuel type.
    for fuel_type in fuel_types:
        # create 10 random samples.
        for _ in range(10):
            pc = random.uniform(0, 100)
            # percentage dead fir + percentage confier cannot exceed 100%
            pdf = random.uniform(0, 100.0 - pc)
            data.append(
                {
                    #   D0 <- input$D0
                    #   SD <- input$SD
                    #   SH <- input$SH
                    #   HR <- input$HR
                    #   GFL <- input$GFL
                    #   CFL <- input$CFL
                    #   ISI <- input$ISI
                    "FUELTYPE": fuel_type,
                    "LAT": random.uniform(40, 70),
                    "LONG": random.uniform(-180, 0),
                    "ELV": random.uniform(0, 5000),
                    "DJ": random.randint(0, 365),
                    "FFMC": random.uniform(0, 100),
                    "BUI": random.uniform(0, 200),
                    "WS": random.uniform(0, 50),
                    "WD": random.uniform(0, 360),
                    "GS": random.uniform(0, 90),
                    "ACCEL": random.randint(0, 1),
                    "ASPECT": random.uniform(0, 360),
                    "BUIEFF": random.randint(0, 1),
                    "HR": random.uniform(0, 24),
                    "THETA": random.uniform(0, 360),
                    "CC": random.uniform(0, 100),
                    "PDF": pdf,
                    "CBH": random.uniform(0, 100),
                    "PC": pc,
                    "FMC": random_fmc(),
                    "GFL": random.uniform(
                        0, 10
                    ),  # Grass Fuel Load (kg/m^2) - default is 0.35
                }
            )
    return data


# def test_slope_calc_again():
#     cffdrs = importr("cffdrs")

#     # Slopecalc fuelType: C6, FFMC: 57.55481411251054, BUI: 133.63769408909872, WS: 16.81983099456876, WAZ: 6.247412014352667, GS: 29.251275109988352, SAZ: 4.474380979600264, FMC: 109.69520000000001, SFC: 3.4742543847234075, PC: null, PDF: null, CC: null, CBH: 7.0, ISI: 0.0, output: WSV
#     # slopeCalc: 110.30912847821551

#     result = cffdrs._Slopecalc(
#         FUELTYPE="C6",
#         FFMC=57.55481411251054,
#         BUI=133.63769408909872,
#         WS=16.81983099456876,
#         WAZ=6.247412014352667,
#         GS=29.251275109988352,
#         SAZ=4.474380979600264,
#         FMC=109.69520000000001,
#         SFC=3.4742543847234075,
#         PC=NULL,
#         PDF=35,
#         CC=80,
#         CBH=7.0,
#         ISI=0.0,
#         output="WSV",
#     )
#     print(result[0])

#     # Slopecalc fuelType: C6, FFMC: 57.55481411251054, BUI: 133.63769408909872, WS: 16.81983099456876, WAZ: 6.247412014352667, GS: 29.251275109988352, SAZ: 4.474380979600264, FMC: 109.69520000000001, SFC: 3.4742543847234075, PC: null, PDF: null, CC: null, CBH: 7.0, ISI: 0.0, output: RAZ
#     # slopeCalc: 4.624313642082066

#     result = cffdrs._Slopecalc(
#         FUELTYPE="C6",
#         FFMC=57.55481411251054,
#         BUI=133.63769408909872,
#         WS=16.81983099456876,
#         WAZ=6.247412014352667,
#         GS=29.251275109988352,
#         SAZ=4.474380979600264,
#         FMC=109.69520000000001,
#         SFC=3.4742543847234075,
#         PC=NULL,
#         PDF=35,
#         CC=80,
#         CBH=7.0,
#         ISI=0.0,
#         output="RAZ",
#     )
#     print(result[0])

#     # dart: ISZ: 0.3454733290959275 = ISIcalc(FFMC: 57.55481411251054, 0)
#     ISZ = cffdrs._ISIcalc(57.55481411251054, 0)
#     print(f"ISZ: {ISZ[0]}")

#     # dart: RSZ: 0.5469080397692441 = ROScalc(fuelType: C6, ISZ: 0.3454733290959275, NoBUI: -1.0, FMC: 109.69520000000001, SFC: 3.4742543847234075, PC: null, PDF: 35.0, CC: 80.0, CBH: 7.0)
#     RSZ = cffdrs._ROScalc(
#         FUELTYPE="C6",
#         ISI=0.3454733290959275,
#         BUI=-1.0,
#         FMC=109.69520000000001,
#         SFC=3.4742543847234075,
#         PC=0,
#         PDF=35.0,
#         CC=80.0,
#         CBH=7.0,
#     )
#     print(f"RSZ: {RSZ[0]}")

#     ROS = cffdrs._C6calc(
#         "C6",
#         0.3454733290959275,
#         -1.0,
#         109.69520000000001,
#         3.4742543847234075,
#         7.0,
#         option="ROS",
#     )
#     print(f"_C6calc: {ROS[0]}")

#     CFB = cffdrs._CFBcalc(
#         "C6", 109.69520000000001, 3.4742543847234075, 0.0006076755997436044, 7.0
#     )
#     print(f"CFB: {CFB[0]}")


def test_slope_calc():
    cffdrs = importr("cffdrs")
    result = cffdrs._Slopecalc(
        "M2",
        98.90994700887234,
        0.0,
        24.695621017090957,
        2.755556900847557,
        76.5953764720197,
        4.855878595311738,
        87.7216,
        1.3797772519962974,
        3.7466175923251854,
        28.721259560328726,
        64.82853387092416,
        6.0,
        0.0,
        output="WSV",
    )
    print("M2 slopecalc: ", result[0])


# def test_slope_calc():
#     cffdrs = importr("cffdrs")
#     base_folder = "./"
#     with open(os.path.join(base_folder, "FBCCalc_input.json"), "r") as f:
#         data = json.load(f)

#     item = data[50]
#     print(item)

#     FUELTYPE = item["FUELTYPE"]
#     WD = item["WD"]
#     LAT = item["LAT"]
#     LONG = item["LONG"]
#     ELV = item["ELV"]
#     DJ = item["DJ"]
#     FFMC = item["FFMC"]
#     BUI = item["BUI"]
#     WS = item["WS"]
#     GS = item["GS"]
#     D0 = 0
#     FMC = None
#     PC = 50
#     PDF = 35
#     CC = 80
#     CBH = 0
#     ISI = 0
#     GFL = 0.35

#     WAZ = WD + pi
#     if WAZ > 2 * pi:
#         WAZ = WAZ - 2 * pi

#     SAZ = item["ASPECT"] + pi
#     if SAZ > 2 * pi:
#         SAZ = SAZ - 2 * pi

#     if FMC is None or FMC <= 0 or FMC > 120:
#         FMC = cffdrs._FMCcalc(LAT=LAT, LONG=LONG, ELV=ELV, DJ=DJ, D0=D0)
#     if FUELTYPE in ["D1", "S1", "S2", "S3", "O1A", "O1B"]:
#         FMC = 0

#     SFC = cffdrs._SFCcalc(FUELTYPE, FFMC, BUI, PC, GFL)

#     wsv = cffdrs._Slopecalc(
#         FUELTYPE=FUELTYPE,
#         FFMC=FFMC,
#         BUI=BUI,
#         WS=WS,
#         WAZ=WAZ,
#         GS=GS,
#         SAZ=SAZ,
#         FMC=FMC,
#         SFC=SFC,
#         PC=PC,
#         PDF=PDF,
#         CC=CC,
#         CBH=CBH,
#         ISI=ISI,
#         output="WSV",
#     )

#     print(f"wsv: {wsv[0]}")


def just_one():
    base_folder = "./"
    with open(os.path.join(base_folder, "FBCCalc_input.json"), "r") as f:
        data = json.load(f)

    item = data[150]
    dataFrame = DataFrame(item)
    cffdrs = importr("cffdrs")
    prediction = cffdrs._FBPcalc(dataFrame, "All")
    result = {}
    for i in range(len(prediction)):
        result[prediction.colnames[i]] = prediction[i][0]
    # print(result)
    for key in ["FMC", "SFC", "WSV", "RAZ"]:
        print(f"{key}: {result[key]}")


def main():
    cffdrs = importr("cffdrs")

    base_folder = "./"

    # with open(os.path.join(base_folder, 'FBCCalc_input.json'), 'r') as f:
    # data = json.load(f)

    data = generate_input_data()
    with open(os.path.join(base_folder, "FBCCalc_input.json"), "w") as f:
        json.dump(data, f, indent=4)
    results = []

    for item in data:
        dataFrame = DataFrame(item)
        prediction = cffdrs._FBPcalc(dataFrame, "All")
        result = {}

        for i in range(len(prediction)):
            result[prediction.colnames[i]] = prediction[i][0]

        results.append(result)

    with open(os.path.join(base_folder, "FBCCalc_output.json"), "w") as f:
        json.dump(results, f, indent=4)

    # print(f'{prediction.colnames[i]}:{prediction[i][0]}')

    # print(f'moo: {result["ID"]}')

    # print('for a in result')
    # for row in result:
    #     print(row)
    # for i in range(result.ncol):
    # print(result[i])
    # for name in result.colnames:
    # print(name)
    # print("result: {}".format(result))


if __name__ == "__main__":
    main()
    # just_one()
    test_slope_calc()
    # test_slope_calc_again()
