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

// function blendColor(p1: number, p2: number): number {
//   if (p1 === 255 && p2 === 255) {
//     return 255
//   } else if (p1 === 255) {
//     return p2
//   } else if (p2 === 255) {
//     return p1
//   }
//   const result = p1 + p2
//   return result === 255 ? 254 : result
// }

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

// function calcROS(ftlNumber: number, isi: number, bui: number): number {
//   if (ftlNumber !== 7) {
//     throw 'not handling this ftl yet'
//   }
//   // C-7 Ponderosa pine/Douglas-fir
//   const column = (bui: number): number => {
//     if (bui < 20) {
//       return 0
//     } else if (bui <= 30) {
//       return 1
//     } else if (bui <= 40) {
//       return 2
//     } else if (bui <= 60) {
//       return 3
//     } else if (bui <= 80) {
//       return 4
//     } else if (bui <= 120) {
//       return 5
//     } else if (bui <= 160) {
//       return 6
//     }
//     return 7
//   }
//   const row = (isi: number): number => {
//     if (isi <= 1) {
//       return 0
//     } else if (isi <= 20) {
//       return Math.round(isi) - 1
//     } else if (isi <= 25) {
//       return 20
//     } else if (isi <= 30) {
//       return 21
//     } else if (isi <= 35) {
//       return 22
//     } else if (isi <= 40) {
//       return 23
//     } else if (isi <= 45) {
//       return 24
//     } else if (isi <= 50) {
//       return 25
//     } else if (isi <= 55) {
//       return 26
//     } else if (isi <= 60) {
//       return 27
//     } else if (isi <= 65) {
//       return 28
//     }
//     return 29
//   }
//   const c7 = [
//     [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1],
//     [0.1, 0.1, 0.1, 0.1, 0.2, 0.2, 0.2, 0.2],
//     [0.2, 0.3, 0.3, 0.3, 0.3, 0.3, 0.4, 0.4],
//     [0.3, 0.5, 0.5, 0.5, 0.6, 0.6, 0.6, 0.6],
//     [0.4, 0.7, 0.8, 0.8, 0.9, 0.9, 0.9, 0.9],
//     [0.6, 1, 1, 1, 1, 1, 1, 1],
//     [0.8, 1, 1, 2, 2, 2, 2, 2],
//     [1, 2, 2, 2, 2, 2, 2, 2],
//     [1, 2, 2, 2, 2, 3, 3, 3],
//     [2, 2, 3, 3, 3, 3, 3, 3],
//     [2, 3, 3, 3, 4, 4, 4, 4],
//     [2, 3, 4, 4, 4, 4, 4, 4],
//     [2, 4, 4, 4, 5, 5, 5, 5],
//     [3, 4, 5, 5, 5, 5, 6, 6],
//     [3, 5, 5, 6, 6, 6, 6, 6],
//     [3, 5, 6, 6, 6, 7, 7, 7],
//     [4, 6, 6, 7, 7, 7, 8, 8],
//     [4, 6, 7, 7, 8, 8, 8, 8],
//     [4, 7, 7, 8, 8, 9, 9, 9],
//     [5, 7, 8, 9, 9, 9, 10, 10],
//     [6, 9, 10, 11, 11, 11, 12, 12],
//     [7, 12, 13, 14, 14, 15, 15, 15],
//     [9, 14, 16, 17, 17, 18, 18, 19],
//     [10, 17, 18, 19, 20, 21, 22, 22],
//     [12, 19, 21, 22, 23, 24, 24, 25],
//     [13, 21, 23, 24, 26, 26, 27, 27],
//     [14, 23, 25, 27, 28, 29, 28, 30],
//     [15, 24, 27, 28, 30, 31, 32, 32],
//     [16, 26, 28, 30, 32, 33, 33, 34],
//     [17, 27, 30, 32, 33, 34, 35, 36]
//   ]

//   return c7[row(isi)][column(bui)]
// }

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

function lookupROS(data: any, ftlNumber: number, isi: number, bui: number) {
  // isi = Math.min(1, isi)
  isi = isi - 1
  if (isi < 0) {
    isi = 0
  } else if (isi > 68) {
    isi = 68
  }
  if (data) {
    if (!('count' in data)) {
      data['count'] = {}
    }
    const count = data['count']
    if (!(ftlNumber in count)) {
      // console.log('there is ftl', ftlNumber)
      count[ftlNumber] = 0
    }
    try {
      if (ftlNumber >= 14 && ftlNumber < 31) {
        // what is this?
        return -1
      } else if (ftlNumber > 31 && ftlNumber < 100) {
        // what is this?
        return -1
      } else if (ftlNumber > 106 && ftlNumber < 425) {
        // what is this?
        return -1
      } else if (ftlNumber >= 500 && ftlNumber < 600) {
        // I think this is M1, with percentage conifer
        if (ftlNumber >= 500 && ftlNumber <= 525) {
          return ['M1'][2]
        } else if (ftlNumber > 525 && ftlNumber < 550) {
          return ['M1'][1]
        }
        return ['M1'][0]
      }
      switch (ftlNumber) {
        case 0:
          // TODO: what is this?
          // I'm going to assume no data.
          return -2
        case 1:
          return data['C1'][isi][bui]
        case 2:
          return data['C2'][isi][bui]
        case 3:
          return data['C3'][isi][bui]
        case 4:
          return data['C4'][isi][bui]
        case 5:
          return data['C5'][isi][bui]
        case 6:
          // what is this?
          return -1
        case 7:
          return data['C7'][isi][bui]
        case 8:
        case 9:
        case 10:
          // what are these?
          return -1
        case 11:
          return data['D1'][isi][bui]
        case 12:
          // D2
          // no lookup
          return -1
        case 13:
          // D1/2
          return data['D1'][isi][bui]
        case 31:
          // grass! need to get the correct lookup
          return -1
        case 99:
          // what are these?
          return -1
        case 100:
          // what is this?
          return -1
        case 101:
          // no fuel
          return -2
        case 102:
          // water!
          return -2
        default:
          count[ftlNumber]++
      }
    } catch (e) {
      console.log(e)
      console.log('ftlNumber', ftlNumber)
      console.log('isi', isi)
      console.log('bui', bui)
      throw e
    }
  }
  return -1
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

function calcROSColour(ros: number, opacity: number): number[] {
  if (ros < 0) {
    if (ros === -2) {
      // it's water - or something that doesn't burn.
      return [0, 0, 0, 0]
    }
    // don't know what this is!
    return [0x0, 0x0, 0x0, opacity]
  }
  // return [0xff, 0x00, 0x00, 0xff]
  return [0xff, Math.max(0, 255 - (ros / 100) * 255), 0x00, opacity]
  // if (ros <= 0.8) {
  //   // dark grey
  //   return [0xa9, 0xa9, 0xa9]
  // } else if (ros <= 3) {
  //   return [0xd3, 0xd3, 0xd3]
  // } else if (ros <= 6) {
  //   return [0xff, 0xc2, 0xc2]
  // } else if (ros <= 13) {
  //   return [0xff, 0x62, 0x00]
  // }
  // return [0xff, 0x00, 0x00]
}

function calcSlopeEquivalentWindSpeed(ftlNumber: number, slope: number): number {
  if (slope < 10) {
    return 0
  } else if (slope < 20) {
    return 2
  } else if (slope < 30) {
    return 5
  } else if (slope < 40) {
    return 9
  } else if (slope < 50) {
    return 13
  } else if (slope < 60) {
    return 17
  } else if (slope < 70) {
    return 21
  }
  return 26
}

const raster = new olSource.Raster({
  sources: [easSource, ftlSource],

  operation: (layers: any, data: any): number[] | ImageData => {
    const eas = layers[0]
    const ftl = layers[1]

    const recover = (eas[0] << 16) | (eas[1] << 8) | eas[2]
    const height = recover >> 11
    const aspectValid = (recover >> 10) & 0x1
    const aspect = (recover >> 7) & 0x7
    const slope = recover & 0x7f
    if (height === 0 || height === 0xffffff || height > data.snowLine) {
      return [0, 0, 0, 0]
    } else {
      const ftlNumber = (ftl[0] << 16) | (ftl[1] << 8) | ftl[2]

      const slopeEquivalentWindSpeed = calcSlopeEquivalentWindSpeed(ftlNumber, slope)
      const slopeAdjustedWindSpeed = slopeEquivalentWindSpeed + data.windSpeed
      const isi = calcISI(data.ffmc, slope, aspect, slopeAdjustedWindSpeed, ftlNumber)
      // const ros = calcROS(ftlNumber, isi, data.bui)
      const ros = lookupROS(
        data.rosLookup,
        ftlNumber,
        Math.round(isi),
        Math.round(data.bui)
      )
      if (ros > data.maxRos) {
        data.maxRos = ros
        // console.log('max ros:', ros)
      }
      return calcROSColour(ros, data.opacity)
      // for C7, ROS maxes out at 36
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
    }
  },
  lib: {
    calcISI: calcISI,
    calcROSColour: calcROSColour,
    calcSlopeEquivalentWindSpeed: calcSlopeEquivalentWindSpeed,
    lookupROS: lookupROS
  }
})
raster.on('beforeoperations', function(event) {
  event.data.opacity = raster.get('opacity')
  event.data.snowLine = raster.get('snowLine')
  event.data.bui = raster.get('bui')
  event.data.ffmc = raster.get('ffmc')
  event.data.windSpeed = raster.get('windSpeed')
  event.data.rosLookup = raster.get('rosLookup')
  event.data.maxRos = 0
})
raster.on('afteroperations', function(event) {
  if (event.data.rosLookup && 'count' in event.data.rosLookup) {
    // console.log('after operations', event.data.rosLookup['count'])
    for (let key in event.data.rosLookup['count']) {
      if (event.data.rosLookup['count'][key] > 0) {
        console.log('what is this?', key)
      }
    }
    // console.log('after operations', event.data.rosLookup['count'])
  }
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
    console.log('fetching lookup data')
    fetch('ros_lookup.json', {
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json'
      }
    })
      .then(response => {
        return response.json()
      })
      .then(json => {
        raster.set('rosLookup', json)
        raster.changed()
      })
  }, [])

  useEffect(() => {
    console.log('input changed')
    raster.set('snowLine', snowLine)
    raster.set('bui', bui)
    raster.set('ffmc', ffmc)
    raster.set('windSpeed', windSpeed)
    raster.set('opacity', opacity)
    raster.changed()
  }, [snowLine, bui, ffmc, windSpeed, opacity])

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
