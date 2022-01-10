import rpy2.robjects as robjs
from rpy2.robjects import DataFrame
from rpy2.robjects.packages import importr
import rpy2.robjects.conversion as cv
from rpy2.rinterface import NULL
import json
import os


def _none2null(_):
    """Turn None values into null"""
    return robjs.r("NULL")


none_converter = cv.Converter("None converter")
none_converter.py2rpy.register(type(None), _none2null)


def main():
    cffdrs = importr("cffdrs")

    base_folder = '../../../fire_behaviour_app/test/resources/'

    with open(os.path.join(base_folder, 'FBCCalc_input.json'), 'r') as f:
        data = json.load(f)

    results = []

    for item in data:
        dataFrame = DataFrame(item)
        prediction = cffdrs._FBPcalc(dataFrame, "All")
        result = {}

        for i in range(len(prediction)):
            result[prediction.colnames[i]] = prediction[i][0]

        results.append(result)

    with open(os.path.join(base_folder, 'FBCCalc_output.json'), 'w') as f:
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
