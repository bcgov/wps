"""
Uses rio-tiler : https://github.com/cogeotiff/rio-tiler
Assumes that S3, AWS settings have been congfigured correctly, e.g.

export AWS_VIRTUAL_HOSTING = "FALSE"
export AWS_S3_ENDPOINT = "some.end.point"
export AWS_ACCESS_KEY_ID = "someaccesskey"
export AWS_SECRET_ACCESS_KEY = "somesecret"
"""
from typing import Final
from starlette.concurrency import run_in_threadpool
from fastapi import FastAPI, Response
from rasterio.errors import RasterioIOError
from fastapi.middleware.cors import CORSMiddleware
from rio_tiler.io import COGReader
from rio_tiler.errors import TileOutsideBounds
from rio_tiler.utils import render
from decouple import config
from cogtiler.util import classify, classify_ftl

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=config('ORIGINS'),
    allow_methods=["GET"]
)

bucket: Final = config('OBJECT_STORE_BUCKET')


@app.get('/{z}/{x}/{y}')
def syncronous_xyz(z: int, x: int, y: int, path: str):
    """ Not sure what's best. Do we make this entire function syncronous? Or
    do we put run each blocking call in the threadpool?
    """
    s3_url = f's3://{bucket}/{path}'
    with COGReader(s3_url) as image:
        try:
            img = image.tile(x, y, z)
        except TileOutsideBounds:
            response = Response(status_code=404)
            response.headers["Cache-Control"] = "max-age=604800"
            return response
        data, mask = classify(img.data)
        del img
    # TODO: This part (`render`) gives an error:
    # "ERROR 4: `/vsimem/xxxx.tif' not recognized as a supported file format."
    # We can replace this with a different method. It's just taking an array of rgba values
    # and turning it into a png file.
    rendered = render(data, mask)
    response = Response(content=rendered, media_type="image/png")
    # cache it for a week - we probably only need to cache for a day or two, but this is on
    # the client, so we don't care.
    response.headers["Cache-Control"] = "max-age=604800"
    return response


@app.get('/value/{band}/{lat}/{lon}')
async def value(band: int, lat: float, lon: float, path: str) -> Response:
    s3_url = f's3://{bucket}/{path}'
    try:
        with await run_in_threadpool(COGReader, s3_url) as image:
            point = await run_in_threadpool(image.point, lon, lat, indexes=band)
            # TODO: put in nice json response. This could even be a nice geojson thing
            return point[band - 1]
    except RasterioIOError:
        # If the file is not found, return 404
        response = Response(status_code=404)
        return response


@app.get('/ftl/{z}/{x}/{y}')
async def xyz(z: int, x: int, y: int, path: str) -> Response:
    """ Not sure what's best. Do we make this entire function syncronous? Or
    do we put run each blocking call in the threadpool?
    TODO: this is really a FTL specific tiler - because of the classification!

    ```bash
    gdal_translate ftl2018.bin ftl_2018.tif -co TILED=YES -co COMPRESS=DEFLATE
    gdaladdo -r nearest ftl_2018.tif 2 4 8 16 32
    gdal_translate ftl_2018.tif ftl_2018_cloudoptimized.tif -co TILED=YES -co COMPRESS=LZW -co COPY_SRC_OVERVIEWS=YES
    ```
    """
    s3_url = f's3://{bucket}/{path}'
    try:
        with await run_in_threadpool(COGReader, s3_url) as image:
            try:
                img = await run_in_threadpool(image.tile, x, y, z)
            except TileOutsideBounds:
                response = Response(status_code=404)
                response.headers["Cache-Control"] = "max-age=604800"
                return response
            data, mask = classify_ftl(img.data)
            del img
    except RasterioIOError:
        # If the file is not found, return 404
        response = Response(status_code=404)
        return response
    # TODO: This part (`render`) gives an error:
    # "ERROR 4: `/vsimem/xxxx.tif' not recognized as a supported file format."
    # We can replace this with a different method. It's just taking an array of rgba values
    # and turning it into a png file.
    rendered = await run_in_threadpool(render, data, mask)
    response = Response(content=rendered, media_type="image/png")
    # cache it for a week - we probably only need to cache for a day or two, but this is on
    # the client, so we don't care.
    # response.headers["Cache-Control"] = "max-age=604800"
    # don't cache while we test this.
    response.headers["Cache-Control"] = "max-age=0"
    return response


@app.get('/tile/{z}/{x}/{y}')
async def xyz(z: int, x: int, y: int, path: str) -> Response:
    """ Not sure what's best. Do we make this entire function syncronous? Or
    do we put run each blocking call in the threadpool?
    TODO: this is really a HFI specific tiler - because of the classification!
    """
    s3_url = f's3://{bucket}/{path}'
    try:
        with await run_in_threadpool(COGReader, s3_url) as image:
            try:
                img = await run_in_threadpool(image.tile, x, y, z)
            except TileOutsideBounds:
                response = Response(status_code=404)
                response.headers["Cache-Control"] = "max-age=604800"
                return response
            data, mask = classify(img.data)
            del img
    except RasterioIOError:
        # If the file is not found, return 404
        response = Response(status_code=404)
        return response
    # TODO: This part (`render`) gives an error:
    # "ERROR 4: `/vsimem/xxxx.tif' not recognized as a supported file format."
    # We can replace this with a different method. It's just taking an array of rgba values
    # and turning it into a png file.
    rendered = await run_in_threadpool(render, data, mask)
    response = Response(content=rendered, media_type="image/png")
    # cache it for a week - we probably only need to cache for a day or two, but this is on
    # the client, so we don't care.
    response.headers["Cache-Control"] = "max-age=604800"
    return response


if __name__ == "__main__":
    # This section of code is for the convenience of developers only. Having this section of code, allows
    # for developers to easily debug the application by running main.py and attaching to it with a debugger.
    # uvicorn is imported in this scope only, as it's not required when the application is run in production.
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8090)
