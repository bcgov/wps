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
            data.append(
                {
                    "FUELTYPE": fuel_type,
                    "LAT": random.uniform(40, 70),
                    "LONG": random.uniform(-180, 0),
                    "ELV": random.uniform(0, 5000),
                    "DJ": random.randint(0, 365),
                    "FFMC": random.uniform(0, 101),
                    "BUI": random.uniform(0, 200),
                    "WS": random.uniform(0, 50),
                    "WD": random.uniform(0, 360),
                    "GS": random.uniform(0, 90),
                    "ACCEL": bool(random.getrandbits(1)),
                    "ASPECT": random.uniform(0, 360),
                    "BUIEFF": bool(random.getrandbits(1)),
                    "MINUTES": random.uniform(0, 1440),
                }
            )
    return data


def test_slope_calc():
    cffdrs = importr("cffdrs")
    base_folder = "./"
    with open(os.path.join(base_folder, "FBCCalc_input.json"), "r") as f:
        data = json.load(f)

    item = data[50]
    print(item)

    FUELTYPE = item["FUELTYPE"]
    WD = item["WD"]
    LAT = item["LAT"]
    LONG = item["LONG"]
    ELV = item["ELV"]
    DJ = item["DJ"]
    FFMC = item["FFMC"]
    BUI = item["BUI"]
    WS = item["WS"]
    GS = item["GS"]
    D0 = 0
    FMC = None
    PC = 50
    PDF = 35
    CC = 80
    CBH = 0
    ISI = 0
    GFL = 0.35

    WAZ = WD + pi
    if WAZ > 2 * pi:
        WAZ = WAZ - 2 * pi

    SAZ = item["ASPECT"] + pi
    if SAZ > 2 * pi:
        SAZ = SAZ - 2 * pi

    if FMC is None or FMC <= 0 or FMC > 120:
        FMC = cffdrs._FMCcalc(LAT=LAT, LONG=LONG, ELV=ELV, DJ=DJ, D0=D0)
    if FUELTYPE in ["D1", "S1", "S2", "S3", "O1A", "O1B"]:
        FMC = 0

    SFC = cffdrs._SFCcalc(FUELTYPE, FFMC, BUI, PC, GFL)

    wsv = cffdrs._Slopecalc(
        FUELTYPE=FUELTYPE,
        FFMC=FFMC,
        BUI=BUI,
        WS=WS,
        WAZ=WAZ,
        GS=GS,
        SAZ=SAZ,
        FMC=FMC,
        SFC=SFC,
        PC=PC,
        PDF=PDF,
        CC=CC,
        CBH=CBH,
        ISI=ISI,
        output="WSV",
    )

    print(f"wsv: {wsv[0]}")


def just_one():
    base_folder = "./"
    with open(os.path.join(base_folder, "FBCCalc_input.json"), "r") as f:
        data = json.load(f)

    item = data[50]
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
    # main()
    # just_one()
    test_slope_calc()
