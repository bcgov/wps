from osgeo import gdal
import numpy as np
import os


def classify(source_path, target_path):

    # Read the source data.
    source_tiff = gdal.Open(source_path, gdal.GA_ReadOnly)
    source_band = source_tiff.GetRasterBand(1)
    source_data = source_band.ReadAsArray()
    # Classify the data.
    classified = np.where(source_data < 4000, 0, source_data)
    classified = np.where((classified >= 4000) & (classified < 10000), 1, classified)
    classified = np.where(classified >= 10000, 2, classified)

    # Remove any existing target file.
    if os.path.exists(target_path):
        os.remove(target_path)
    output_driver = gdal.GetDriverByName("GTiff")
    # Create an object with the same dimensions as the input.
    # gdal.GDT_Int16 ?
    target_tiff = output_driver.Create(target_path, xsize=source_band.XSize,
                                       ysize=source_band.YSize, bands=1, eType=gdal.GDT_Int16)
    # Set the geotransform and projection to the same as the input.
    target_tiff.SetGeoTransform(source_tiff.GetGeoTransform())
    target_tiff.SetProjection(source_tiff.GetProjection())

    # Write the classified data to the band.
    outband = target_tiff.GetRasterBand(1)
    outband.SetNoDataValue(0)
    outband.WriteArray(classified)

    # Important to make sure data is flushed to disk!
    target_tiff.FlushCache()

    # explicit delete to make sure underlying resources are cleared up!
    del source_band
    del source_tiff
    del target_tiff


def main():
    # get the tiff from : \\wildfiregeo.bcgov\geomatics$\!Data_Exchange\Data\SFMS_forecast_tiffs
    classify('hfi20220720.tif', 'hfi_classified.tif')


if __name__ == '__main__':
    main()
