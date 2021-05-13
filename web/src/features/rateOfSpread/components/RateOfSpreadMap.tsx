import React, { useEffect, useState } from 'react'
import * as olSource from 'ol/source'
import { fromLonLat } from 'ol/proj'
import Map, { RedrawCommand } from 'features/map/Map'
import TileLayer from 'features/map/TileLayer'
import ImageLayer from 'features/map/ImageLayer'
// import * as thing from 'utils/fbp.js'

export const CENTER_OF_BC = [-125.5, 54.2]
const zoom = 6

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

const ftlFullSource = new olSource.XYZ({
  url: getUrl('FTLFULL'),
  crossOrigin: 'anonymous'
})

const elevationSource = new olSource.XYZ({
  url: getUrl('ELEVATION'),
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
      } else if (ftlNumber >= 400 && ftlNumber < 600) {
        // I think this is M1, with percentage conifer
        const conifer = ftlNumber % 100
        if (conifer >= 0 && conifer <= 25) {
          return ['M1'][2]
        } else if (conifer > 25 && conifer < 50) {
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

function ISIcalc(ffmc: number, ws: number, fbpMod: boolean = false): number {
  /*
  #############################################################################
  # Description:
  #   Computes the Initial Spread Index From the FWI System. Equations are from
  #   Van Wagner (1985) as listed below, except for the modification for fbp
  #   takene from FCFDG (1992).
  
  #   Equations and FORTRAN program for the Canadian Forest Fire 
  #   Weather Index System. 1985. Van Wagner, C.E.; Pickett, T.L. 
  #   Canadian Forestry Service, Petawawa National Forestry 
  #   Institute, Chalk River, Ontario. Forestry Technical Report 33. 
  #   18 p.
  #
  #   Forestry Canada  Fire Danger Group (FCFDG) (1992). Development and 
  #   Structure of the Canadian Forest Fire Behavior Prediction System."  
  #   Technical ReportST-X-3, Forestry Canada, Ottawa, Ontario.
  #
  # Args:
  #   ffmc:   Fine Fuel Moisture Code
  #     ws:   Wind Speed (km/h)
  # fbpMod:   TRUE/FALSE if using the fbp modification at the extreme end
  #
  # Returns:
  #   ISI:    Intial Spread Index
  #
  #############################################################################
  */
  // #Eq. 10 - Moisture content
  // fm <- 147.2 * (101 - ffmc)/(59.5 + ffmc)
  const fm = (147.2 * (101 - ffmc)) / (59.5 + ffmc)
  // #Eq. 24 - Wind Effect
  // #the ifelse, also takes care of the ISI modification for the fbp functions
  // # This modification is Equation 53a in FCFDG (1992)
  // fW   <- ifelse(ws >= 40 & fbpMod==TRUE,
  //                12 * (1 - exp(-0.0818 * (ws - 28))),
  //                exp(0.05039 * ws))
  const fW =
    ws >= 40 && fbpMod ? 12 * (1 - Math.exp(-0.0818 * (ws - 28))) : Math.exp(0.05039 * ws)
  // #Eq. 25 - Fine Fuel Moisture
  // fF <- 91.9 * exp(-0.1386 * fm) * (1 + (fm^5.31) / 49300000)
  const fF = 91.9 * Math.exp(-0.1386 * fm) * (1 + Math.pow(fm, 5.31) / 49300000)
  // #Eq. 26 - Spread Index Equation
  // isi <- 0.208 * fW * fF
  return 0.208 * fW * fF
  // return(isi)
}

// function calcISI(
//   ffmc: number,
//   slope: number,
//   aspect: number,
//   windSpeed: number,
//   ftlNumber: number
// ): number {
//   const _isi = (ffmcs: number, wspd: number): number => {
//     /*
//     TODO: credit:
//     *   Created for Alaska Fire & Fuels, by MesoWest
//     *
//     *   Author: Joe Young
//     *   Date: 25 January 2016
//     *   Mod: 28 June 2016
//     *   Mod: 27 April 2017
//     */
//     // initial spread index
//     const fm = (147.2 * (101.0 - ffmcs)) / (59.5 + ffmcs)
//     const sf = 19.115 * Math.exp(-0.1386 * fm) * (1.0 + Math.pow(fm, 5.31) / 4.93e7)
//     return sf * Math.exp(0.05039 * wspd)
//   }
//   return _isi(ffmc, windSpeed)
// }

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

function ftlNumberToFtlCode(ftlNumber: number): string | undefined {
  switch (ftlNumber) {
    case 1:
      return 'C1'
    case 2:
      return 'C2'
    case 3:
      return 'C3'
    case 4:
      return 'C4'
    case 5:
      return 'C5'
    case 7:
      return 'C7'
    case 11:
      return 'D1'
    case 13:
      return 'D2'
  }
  return undefined
}

function isNonFuel(ftlNumber: number): boolean {
  switch (ftlNumber) {
    case 101:
    case 102:
    case 106:
      return true
  }
  return false
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

export function ROScalc(
  FUELTYPE: string,
  ISI: number,
  BUI: number,
  FMC: number | undefined = undefined,
  SFC: number | undefined = undefined,
  PC: number | undefined = undefined,
  PDF: number | undefined = undefined,
  CC: number | undefined = undefined,
  CBH: number | undefined = undefined
): number {
  const NoBUI = -1
  const d = [
    'C1',
    'C2',
    'C3',
    'C4',
    'C5',
    'C6',
    'C7',
    'D1',
    'M1',
    'M2',
    'M3',
    'M4',
    'S1',
    'S2',
    'S3',
    'O1A',
    'O1B'
  ]
  const a = [90, 110, 110, 110, 30, 30, 45, 30, 0, 0, 120, 100, 75, 40, 55, 190, 250]
  const b = [
    0.0649,
    0.0282,
    0.0444,
    0.0293,
    0.0697,
    0.08,
    0.0305,
    0.0232,
    0,
    0,
    0.0572,
    0.0404,
    0.0297,
    0.0438,
    0.0829,
    0.031,
    0.035
  ]
  const c0 = [
    4.5,
    1.5,
    3.0,
    1.5,
    4.0,
    3.0,
    2.0,
    1.6,
    0,
    0,
    1.4,
    1.48,
    1.3,
    1.7,
    3.2,
    1.4,
    1.7
  ]

  const index = d.indexOf(FUELTYPE)

  let rsi = -1

  // Eq. 26 (FCFDG 1992) - Initial Rate of Spread for Conifer and Slash types
  // RSI <- ifelse(FUELTYPE %in% c("C1", "C2", "C3", "C4", "C5", "C7", "D1", "S1",
  //                               "S2", "S3"),
  //         as.numeric(a[FUELTYPE] * (1 - exp(-b[FUELTYPE] * ISI))**c0[FUELTYPE]),
  //         RSI)
  if (['C1', 'C2', 'C3', 'C4', 'C5', 'C7', 'D1', 'S1', 'S2', 'S3'].includes(FUELTYPE)) {
    rsi = Math.pow(a[index] * (1 - Math.exp(-b[index] * ISI)), c0[index])
  }
  // #Eq. 27 (FCFDG 1992) - Initial Rate of Spread for M1 Mixedwood type
  // RSI <- ifelse(FUELTYPE %in% c("M1"),
  //           PC/100 *
  //             .ROScalc(rep("C2", length(ISI)),ISI,NoBUI,FMC,SFC,PC,PDF,CC,CBH)
  //             + (100 - PC) / 100 *
  //             .ROScalc(rep("D1", length(ISI)),ISI,NoBUI,FMC,SFC,PC,PDF,CC, CBH),
  //           RSI)
  else if (FUELTYPE === 'M1') {
    if (!PC) {
      throw 'PC not specified'
    }
    rsi =
      (PC / 100) * ROScalc('C2', ISI, NoBUI, FMC, SFC, PC, PDF, CC, CBH) +
      ((100 - PC) / 100) * ROScalc('D1', ISI, NoBUI, FMC, SFC, PC, PDF, CC, CBH)
  }
  // #Eq. 27 (FCFDG 1992) - Initial Rate of Spread for M2 Mixedwood type
  // RSI <- ifelse(FUELTYPE %in% c("M2"),
  //           PC/100 *
  //             .ROScalc(rep("C2", length(ISI)),ISI,NoBUI,FMC,SFC,PC,PDF,CC,CBH)
  //             + 0.2*(100-PC)/100 *
  //             .ROScalc(rep("D1", length(ISI)),ISI,NoBUI,FMC,SFC,PC,PDF,CC, CBH),
  //           RSI)
  else if (FUELTYPE === 'M2') {
    if (!PC) {
      throw 'PC not specified'
    }
    rsi =
      (PC / 100) * ROScalc('C2', ISI, NoBUI, FMC, SFC, PC, PDF, CC, CBH) +
      ((0.2 * (100 - PC)) / 100) * ROScalc('D1', ISI, NoBUI, FMC, SFC, PC, PDF, CC, CBH)
  } else {
    // throw 'not implemented for ' + FUELTYPE
  }

  return rsi
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
      const isi = ISIcalc(data.ffmc, slopeAdjustedWindSpeed)
      const ftlCode = ftlNumberToFtlCode(ftlNumber)

      let ros = -1
      if (ftlCode) {
        ros = ROScalc(ftlCode, isi, data.bui)
        if (ftlNumber in data.info['known']) {
          data.info['known'][ftlNumber]++
        } else {
          data.info['known'][ftlNumber] = 1
        }
      } else {
        if (isNonFuel(ftlNumber)) {
          ros = -2
          if (ftlNumber in data.info['known']) {
            data.info['known'][ftlNumber]++
          } else {
            data.info['known'][ftlNumber] = 1
          }
        } else {
          if (ftlNumber in data.info['unknown']) {
            data.info['unknown'][ftlNumber]++
          } else {
            data.info['unknown'][ftlNumber] = 1
          }
        }
      }

      // ros = lookupROS(data.rosLookup, ftlNumber, Math.round(isi), Math.round(data.bui))
      // const ros = calcROS(ftlNumber, isi, data.bui)

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
    ISIcalc: ISIcalc,
    calcROSColour: calcROSColour,
    calcSlopeEquivalentWindSpeed: calcSlopeEquivalentWindSpeed,
    ftlNumberToFtlCode: ftlNumberToFtlCode,
    lookupROS: lookupROS,
    ROScalc: ROScalc,
    isNonFuel: isNonFuel
  }
})
raster.on('beforeoperations', function(event) {
  event.data.opacity = raster.get('opacity')
  event.data.snowLine = raster.get('snowLine')
  event.data.bui = raster.get('bui')
  event.data.ffmc = raster.get('ffmc')
  event.data.windSpeed = raster.get('windSpeed')
  event.data.rosLookup = raster.get('rosLookup')
  event.data.info = raster.get('info')
  event.data.maxRos = 0
})
raster.on('afteroperations', function(event) {
  if (event.data.info) {
    // console.log('known:')
    // for (let key in event.data.info['known']) {
    //   console.log(`${key}: ${event.data.info['known'][key]}`)
    // }
    console.log('unknown:')
    for (let key in event.data.info['unknown']) {
      console.log(`${key}: ${event.data.info['unknown'][key]}`)
    }
  }
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
    raster.set('info', { known: {}, unknown: {} })
    raster.changed()
  }, [])

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
      {/* <TileLayer source={elevationSource} /> */}
      <TileLayer source={source} />
      <ImageLayer source={raster} />
    </Map>
  )
}

export default React.memo(RateOfSpreadMap)
