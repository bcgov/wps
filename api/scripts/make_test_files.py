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


def main():
    cffdrs = importr("cffdrs")

    dataFrame = DataFrame(
        {
            "FUELTYPE": "C1",
            "LAT": 80.0,
            "LONG": 100.0,
            "ELV": 100.0,
            "DJ": 10,
            "FFMC": 10.0,
            "BUI": 10.0,
            "WS": 10.0,
            "WD": 10.0,
            "GS": 10.0,
            "ACCEL": 1,
            "ASPECT": 10.0,
            "BUIEFF": 1,
            "MINUTES": 60.0,
        }
    )
    result = cffdrs._FBPcalc(dataFrame, "Primary")
    print("result: {}".format(result))


if __name__ == "__main__":
    main()
