""" Process DEM files
- iterate through dem files
- generate slope
- generate aspect
- generate 3 band raster
"""
import os
import subprocess
import struct
from pathlib import Path
import tempfile
from osgeo import gdal
import numpy


def get_int32_array(band, y: int):
    """ get row y in band as int array """
    scanline = band.ReadRaster(xoff=0, yoff=y,
                               xsize=band.XSize, ysize=1,
                               buf_xsize=band.XSize, buf_ysize=1,
                               buf_type=gdal.GDT_Int32)
    return struct.unpack('i' * band.XSize, scanline)


def get_float32_array(band, y: int):
    """ get row y in band as float array """
    scanline = band.ReadRaster(xoff=0, yoff=y,
                               xsize=band.XSize, ysize=1,
                               buf_xsize=band.XSize, buf_ysize=1,
                               buf_type=gdal.GDT_Float32)
    return struct.unpack('f' * band.XSize, scanline)


def dem_files(path) -> os.DirEntry:
    """ yield up al lthe .dem files """
    for entry in os.scandir(path):
        if entry.is_dir(follow_symlinks=False):
            yield from dem_files(entry.path)
        elif entry.path.endswith('.dem'):
            yield entry


def generate_aspect(dem_path: str) -> str:
    """
    gdaldem aspect [source file] [target file] -of GTiff -b 1 -zero_for_flat
    """
    target = f'{os.path.splitext(os.path.join(Path(dem_path).parent, Path(dem_path).name))[0]}-aspect.tif'
    if os.path.exists(target):
        os.remove(target)
    command = f'gdaldem aspect {dem_path} {target} -of GTiff -b 1 -zero_for_flat'
    print(command)
    os.system(command)
    return target


def generate_slope(dem_path: str) -> str:
    """
    Slope in percentage.

    gdaldem slope [source file] [target file] -of GTiff -b 1 -s 1.0 -p
    """
    target = f'{os.path.splitext(os.path.join(Path(dem_path).parent, Path(dem_path).name))[0]}-slope.tif'
    if os.path.exists(target):
        os.remove(target)
    command = f'gdaldem slope {dem_path} {target} -of GTiff -b 1 -s 1.0 -p'
    print(command)
    os.system(command)
    return target


def reproject_dem(dem_path: str):
    """
    gdalwarp -t_srs EPSG:3857 -r near -of GTiff [source]] [target]

    EPSG:4326 - WGS84
    EPSG:3857 - Pseudo-Mercator -- Spherical Mercator, Google Maps, OpenStreetMap, Bing, ArcGIS, ESRI

    """
    target = f'{os.path.splitext(os.path.join(Path(dem_path).parent, Path(dem_path).name))[0]}.tif'
    if os.path.exists(target):
        os.remove(target)
    command = f'gdalwarp -t_srs EPSG:4326 -r near -of GTiff {dem_path} {target}'
    print(command)
    os.system(command)
    return target


def make_target_eas_path(dem_path: str, target_path: str):
    return f'{os.path.join(target_path, os.path.splitext(Path(dem_path).name)[0])}-eas-3band.tif'


def generate_rgb(dem_path: str, slope_path: str, aspect_path: str, output_path: str):
    # read input file
    elevation_ds = gdal.Open(dem_path)
    aspect_ds = gdal.Open(aspect_path)
    slope_ds = gdal.Open(slope_path)
    try:
        # they all have the same projection and transformation...
        projection = elevation_ds.GetProjection()
        geotransform = elevation_ds.GetGeoTransform()

        elevation_band = elevation_ds.GetRasterBand(1)
        aspect_band = aspect_ds.GetRasterBand(1)
        slope_band = slope_ds.GetRasterBand(1)

        print("Projection={}".format(projection))
        print("Geogransform={}".format(geotransform))
        print("Elevation Band Type={}".format(gdal.GetDataTypeName(elevation_band.DataType)))
        print("Aspect Band Type={}".format(gdal.GetDataTypeName(aspect_band.DataType)))
        print("Slope Band Type={}".format(gdal.GetDataTypeName(slope_band.DataType)))
        print(f'band.XSize: {elevation_band.XSize}')
        print(f'band.YSize: {elevation_band.YSize}')

        # create output file
        driver = gdal.GetDriverByName("GTiff")
        outdata = driver.Create(output_path, elevation_band.XSize, elevation_band.YSize, 3, gdal.GDT_Byte)
        try:
            outdata.SetProjection(projection)
            outdata.SetGeoTransform(geotransform)

            r_band = outdata.GetRasterBand(1)
            r_band.SetColorInterpretation(gdal.GCI_RedBand)

            g_band = outdata.GetRasterBand(2)
            g_band.SetColorInterpretation(gdal.GCI_GreenBand)

            b_band = outdata.GetRasterBand(3)
            b_band.SetColorInterpretation(gdal.GCI_BlueBand)

            for y in range(elevation_band.YSize):
                if y % 200 == 0:
                    print(f'{y / elevation_band.YSize * 100}% done')

                elevation_array = get_int32_array(elevation_band, y)
                aspect_array = get_float32_array(aspect_band, y)
                slope_array = get_float32_array(slope_band, y)

                r_array, g_array, b_array = [], [], []
                r_array.append([])
                g_array.append([])
                b_array.append([])

                for elevation, aspect, slope in zip(elevation_array, aspect_array, slope_array):
                    # print(f'elevation:{elevation}')
                    # shift elevation left 11 bits
                    value = (elevation << 11)
                    # is the aspect valid? (flat ground doesn't have an aspect!)
                    valid_aspect = aspect >= 0 and aspect <= 360
                    value = value | valid_aspect << 10
                    # simplify the aspect
                    aspect = int(aspect / 45) & 0x7
                    value = value | aspect << 7
                    # 7 bits left for the slope
                    if slope < 0 or slope > 360:
                        # we just assume 0 for the slope if there is none.
                        slope = 0
                    value = value | int(slope) & 0x7F

                    # print(f'value:{value}'')

                    r_array[0].append((value >> 16) & 0xff)
                    g_array[0].append((value >> 8) & 0xff)
                    b_array[0].append(value & 0xff)

                r_band.WriteArray(numpy.array(r_array), xoff=0, yoff=y)
                g_band.WriteArray(numpy.array(g_array), xoff=0, yoff=y)
                b_band.WriteArray(numpy.array(b_array), xoff=0, yoff=y)

            outdata.FlushCache()
        finally:
            del outdata

    finally:
        del elevation_ds
        del aspect_ds
        del slope_ds

    return output_path


def main():
    """
    # find each dem file
    # re-project
    # generate slope
    # generate aspec
    # create 3 band raster
    """
    dem_dir = '/home/sybrand/Downloads/Work/topo/mtec'
    target_dir = '/home/sybrand/Workspace/wps/openshift/mapserver/docker/etc/mapserver/eas'
    with tempfile.TemporaryDirectory() as temporary_path:
        for dem_entry in dem_files(dem_dir):
            print(dem_entry.path)
            output_path = make_target_eas_path(dem_entry.path, target_dir)
            if os.path.exists(output_path):
                print(f'{output_path} alread exists - skipping')
            else:
                reprojected_dem = reproject_dem(dem_entry.path)
                slope_path = generate_slope(reprojected_dem)
                aspect_path = generate_aspect(reprojected_dem)
                intermediate_path = make_target_eas_path(reprojected_dem, temporary_path)
                generate_rgb(reprojected_dem, slope_path, aspect_path, intermediate_path)
                os.rename(intermediate_path, output_path)
                # p = subprocess.Popen(['gdaltindex eas-3band-tif.shp *.tif', ], cwd=target_dir)
                # p.wait()
    # gdaltindex eas-3band-tif.shp *.tif
    print(target_dir)
    print('remember to run: gdaltindex eas-3band-tif.shp *.tif')


def another_main():
    mega_topo = '/home/sybrand/Workspace/wps/openshift/mapserver/docker/etc/mapserver/mega_merged_topo.tif'
    slope_path = generate_slope(mega_topo)
    aspect_path = generate_aspect(mega_topo)
    generate_rgb(mega_topo, slope_path, aspect_path,
                 '/home/sybrand/Workspace/wps/openshift/mapserver/docker/etc/mapserver/mega_merged_topo_eas.tif')


if __name__ == '__main__':
    # main()
    another_main()
