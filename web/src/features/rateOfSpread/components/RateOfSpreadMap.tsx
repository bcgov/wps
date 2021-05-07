import React, { useEffect, useState } from 'react'
import * as olSource from 'ol/source'
import { fromLonLat } from 'ol/proj'
import Map, { RedrawCommand } from 'features/map/Map'
import TileLayer from 'features/map/TileLayer'
import ImageLayer from 'features/map/ImageLayer'

export const CENTER_OF_BC = [-121.5, 51.4]
const zoom = 9

const BC_ROAD_BASE_MAP_SERVER_URL =
  'https://maps.gov.bc.ca/arcgis/rest/services/province/roads_wm/MapServer'

// Static source is allocated since our tile source does not change and
// a new source is not allocated every time WeatherMap is re-rendered,
// which causes the TileLayer to re-render.
const source = new olSource.XYZ({
  url: `${BC_ROAD_BASE_MAP_SERVER_URL}/tile/{z}/{y}/{x}`,
  // Normally we would get attribution text from `${BC_ROAD_BASE_MAP_SERVER_URL}?f=pjson`
  // however this endpoint only allows the origin of http://localhost:3000, so the text has been just copied from that link
  attributions: 'Government of British Columbia, DataBC, GeoBC'
})

// const demSource = new olSource.TileImage({
//   tileUrlFunction: (coordinate, pixelRatio, projection): string => {
//     console.log('coordinate, pixelRatio, projection', coordinate, pixelRatio, projection)
//     return (
//       'http://0.0.0.0:8000/' +
//       coordinate[0] +
//       '/' +
//       coordinate[1] +
//       '/' +
//       (-coordinate[2] - 1) +
//       '.png'
//     )
//   }
// })

const getUrl = (layer: string) => {
  return `http://localhost/cgi-bin/mapserv?map=/home/sybrand/Workspace/wps/mapserver/sigh.map&MODE=tile&TILEMODE=gmap&LAYERS=${layer}&TILE={x}+{y}+{z}`
}

// const layers = 'FTL'
// const layers = 'DEM'
// const layers = 'DEM2'
// const layers = 'SLOPE'
// const layers = 'ASPECT'
const ftlSource = new olSource.XYZ({
  url: getUrl('FTL'),
  crossOrigin: 'anonymous'
})

const slopeSource = new olSource.XYZ({
  url: getUrl('SLOPE'),
  crossOrigin: 'anonymous'
})

const aspectSource = new olSource.XYZ({
  url: getUrl('ASPECT'),
  crossOrigin: 'anonymous'
})

const demSource = new olSource.XYZ({
  url: getUrl('DEM'),
  crossOrigin: 'anonymous'
})

const dem2Source = new olSource.XYZ({
  url: getUrl('DEM2'),
  crossOrigin: 'anonymous'
})

const dem3Source = new olSource.XYZ({
  url: getUrl('DEM3'),
  crossOrigin: 'anonymous'
})

function blendColor(p1: number, p2: number): number {
  if (p1 === 255 && p2 === 255) {
    return 255
  } else if (p1 === 255) {
    return p2
  } else if (p2 === 255) {
    return p1
  }
  const result = p1 + p2
  return result === 255 ? 254 : result
}

const raster = new olSource.Raster({
  sources: [dem2Source],

  operation: (pixels: any, data: any): number[] | ImageData => {
    const pixel = pixels[0]
    const height =
      ((pixel[0] & 0xff) << 16) | ((pixel[1] & 0xff) << 8) | (pixel[2] & 0xff)
    if (height === 0 || height == 0xffffff || height > data.snowLine) {
      pixel[3] = 0
    } else {
      if (height >= 0 && height <= 1000) {
        pixel[0] = 0
        pixel[1] = 0
        pixel[2] = 255
      } else if (height > 1000 && height <= 2000) {
        pixel[0] = 0
        pixel[1] = 255
        pixel[2] = 0
      } else {
        pixel[0] = 255
        pixel[1] = 0
        pixel[2] = 0
      }
      pixel[3] = data.opacity
    }
    return pixel
    // const slopePixels = pixels[0]
    // const ftlPixels = pixels[1]
    // // var value = vgi(pixel)
    // // summarize(value, data.counts)
    // // if (value >= data.threshold) {
    // //   pixel[0] = 0
    // //   pixel[1] = 255
    // //   pixel[2] = 0
    // //   pixel[3] = 128
    // // } else {
    // //   pixel[3] = 0
    // // }
    // // return it unchanged
    // // if (pixel[1] !== 0) {
    // //   pixel[0] = 255
    // //   pixel[1] = 128
    // // }
    // // pixel[1] = 100
    // const pixel = [
    //   blendColor(slopePixels[0], ftlPixels[0]),
    //   blendColor(slopePixels[1], ftlPixels[1]),
    //   blendColor(slopePixels[2], ftlPixels[2]),
    //   255
    // ]
    // if (pixel[0] === 255 && pixel[1] === 255 && pixel[2] === 255) {
    //   pixel[3] = 0
    // } else {
    //   pixel[3] = data.moo
    // }
    // // if (pixel[0] !== 0 || pixel[1] !== 0 || pixel[2] !== 0) {
    // //   pixel[0] = 255
    // //   pixel[1] = 0
    // //   pixel[2] = 0
    // //   pixel[3] = 128
    // //   // console.log(pixel)
    // // }
    // // pixel[3] = 128
    // return pixel
  },
  lib: {
    blendColor: blendColor
  }
})
raster.on('beforeoperations', function(event) {
  event.data.opacity = raster.get('opacity')
  event.data.snowLine = raster.get('snowLine')
})

interface Props {
  snowLine: number
}

const RateOfSpreadMap = ({ snowLine }: Props) => {
  raster.set('opacity', 128)

  const [center, setCenter] = useState(fromLonLat(CENTER_OF_BC))

  useEffect(() => {
    raster.set('snowLine', snowLine)
    raster.changed()
  }, [snowLine])

  return (
    <Map
      center={center}
      setMapCenter={(newCenter: number[]) => {
        setCenter(newCenter)
      }}
      isCollapsed={false}
      zoom={zoom}
      redrawFlag={{ redraw: false } as RedrawCommand}
    >
      <TileLayer source={source} />
      {/* <TileLayer source={ftlSource} opacity={0.5} /> */}
      <ImageLayer source={raster} />
      {/* <div>
        <Typography id="discrete-slider-small-steps" gutterBottom>
          Snow line
        </Typography>
        <Slider
          aria-label="Snow line"
          step={100}
          min={0}
          max={5000}
          defaultValue={5000}
          marks={true}
          valueLabelDisplay="auto"
        ></Slider>
        <button
          onClick={() => {
            increaseOpacity()
          }}
        >
          Increase
        </button>
        <button
          onClick={() => {
            decreaseOpacity()
          }}
        >
          Decrease
        </button>
      </div> */}
    </Map>
  )
}

export default React.memo(RateOfSpreadMap)
