
from osgeo import gdal
import numpy as np

PATH = "/Users/dareboss/Documents/tpi/"


def main():
    fname = f"{PATH}bc_dem_2000_tpi_11_class3.tif"
    ds = gdal.Open(fname, gdal.GA_ReadOnly)
    band = ds.GetRasterBand(1)
    data = band.ReadAsArray()

    class1 = data[data == 1]
    class2 = data[data == 2]
    class3 = data[data == 3]

    sum = len(class1) + len(class2) + len(class3)
    c1len = len(class1)
    c2len = len(class2)
    c3len = len(class3)

    print(f"Valley bottom: {c1len/sum *100:.1f}")
    print(f"Mid slope: {c2len/sum *100:.1f}")
    print(f"Upper slope: {c3len/sum *100:.1f}")

    ds = None


if __name__ == "__main__":
    main()