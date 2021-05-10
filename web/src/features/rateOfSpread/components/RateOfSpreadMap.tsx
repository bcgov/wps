import React, { useEffect, useState } from 'react'
import * as olSource from 'ol/source'
import { fromLonLat } from 'ol/proj'
import Map, { RedrawCommand } from 'features/map/Map'
import TileLayer from 'features/map/TileLayer'
import ImageLayer from 'features/map/ImageLayer'
// import * as thing from 'utils/fbp.js'

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

// function rateOfSpread(fuelType: FuelType, isi: number, bui: number): number {

// }

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
  return `http://localhost:8081/cgi-bin/mapserv?map=/etc/mapserver/mapserver.map&MODE=tile&TILEMODE=gmap&LAYERS=${layer}&TILE={x}+{y}+{z}`
  // return `http://localhost:80/cgi-bin/mapserv?map=/home/sybrand/Workspace/wps/mapserver/sigh.map&MODE=tile&TILEMODE=gmap&LAYERS=${layer}&TILE={x}+{y}+{z}`
}

const ftlSource = new olSource.XYZ({
  url: getUrl('FTL'),
  crossOrigin: 'anonymous'
})

const easSource = new olSource.XYZ({
  url: getUrl('EAS'),
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

function calcROS(ftlNumber: number, isi: number, bui: number): number {
  if (ftlNumber !== 7) {
    throw 'not handling this ftl yet'
  }
  // C-7 Ponderosa pine/Douglas-fir

  return isi
}

function calcISI(
  ffmc: number,
  slope: number,
  aspect: number,
  windSpeed: number,
  ftlNumber: number
): number {
  const _isi = (ffmcs: number, wspd: number): number => {
    /*
    TODO: credit:
    *   Created for Alaska Fire & Fuels, by MesoWest
    *
    *   Author: Joe Young 
    *   Date: 25 January 2016
    *   Mod: 28 June 2016
    *   Mod: 27 April 2017
    */
    // initial spread index
    const fm = (147.2 * (101.0 - ffmcs)) / (59.5 + ffmcs)
    const sf = 19.115 * Math.exp(-0.1386 * fm) * (1.0 + Math.pow(fm, 5.31) / 4.93e7)
    return sf * Math.exp(0.05039 * wspd)
  }
  return _isi(ffmc, windSpeed)
}

const raster = new olSource.Raster({
  sources: [easSource, ftlSource],

  operation: (layers: any, data: any): number[] | ImageData => {
    const eas = layers[0]
    const ftl = layers[1]
    const result = [0, 0, 0, 0]

    const recover = (eas[0] << 16) | (eas[1] << 8) | eas[2]
    const height = recover >> 11
    const aspectValid = (recover >> 10) & 0x1
    const aspect = (recover >> 7) & 0x7
    const slope = recover & 0x7f
    if (height === 0 || height === 0xffffff || height > data.snowLine) {
      result[3] = 0
    } else {
      const ftlNumber = (ftl[0] << 16) | (ftl[1] << 8) | ftl[2]
      if (ftlNumber === 7) {
        const isi = calcISI(data.ffmc, slope, aspect, data.windSpeed, ftlNumber)
        const r = calcROS(ftlNumber, isi, data.bui)
        // for C7, ROS maxes out at 36
        result[0] = (r / 36) * 255
        result[1] = 0
        result[2] = 0
        result[3] = data.opacity
      } else {
        // not doing this right now
        result[0] = 0
        result[1] = 0
        result[2] = 128
        result[3] = data.opacity
      }
      // if (aspectValid) {
      //   switch (aspect) {
      //     case 7:
      //     case 0:
      //       // north
      //       result[0] = 255
      //       break
      //     case 1:
      //     case 2:
      //       // east
      //       result[1] = 255
      //       break
      //     case 3:
      //     case 4:
      //       // south
      //       result[2] = 255
      //       break
      //     case 5:
      //     case 6:
      //       // west
      //       result[0] = 255
      //       result[2] = 255
      //       break
      //     default:
      //       // error!
      //       result[0] = 255
      //       result[1] = 255
      //       result[2] = 255
      //   }
      //   result[3] = 255
      // } else {
      //   result[0] = 0
      //   result[1] = 0
      //   result[2] = 0
      //   result[3] = 255
      // }

      // 257 to 2390
      // const adjust = ((height - 257) / 2133) * 255
      // result[0] = adjust
      // result[1] = adjust
      // result[2] = adjust
      // result[3] = 255
    }
    return result
  },
  lib: {
    blendColor: blendColor,
    calcROS: calcROS,
    calcISI: calcISI
  }
})
raster.on('beforeoperations', function(event) {
  event.data.opacity = raster.get('opacity')
  event.data.snowLine = raster.get('snowLine')
  event.data.bui = raster.get('bui')
  event.data.ffmc = raster.get('ffmc')
  event.data.windSpeed = raster.get('windSpeed')
})

interface Props {
  snowLine: number
  bui: number
  ffmc: number
  windSpeed: number
  opacity: number
}

const RateOfSpreadMap = ({ snowLine, bui, ffmc, windSpeed, opacity }: Props) => {
  const [center, setCenter] = useState(fromLonLat(CENTER_OF_BC))

  useEffect(() => {
    raster.set('snowLine', snowLine)
    raster.changed()
  }, [snowLine])

  useEffect(() => {
    raster.set('bui', bui)
    raster.changed()
  }, [bui])

  useEffect(() => {
    raster.set('ffmc', ffmc)
    raster.changed()
  }, [ffmc])

  useEffect(() => {
    raster.set('windSpeed', windSpeed)
    raster.changed()
  }, [windSpeed])

  useEffect(() => {
    raster.set('opacity', opacity)
    raster.changed()
  }, [opacity])

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
      <ImageLayer source={raster} />
    </Map>
  )
}

export default React.memo(RateOfSpreadMap)
