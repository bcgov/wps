import React, { useEffect, useState } from 'react'
import * as olSource from 'ol/source'
import { fromLonLat } from 'ol/proj'
import Map, { RedrawCommand } from 'features/map/Map'
import TileLayer from 'features/map/TileLayer'
import ImageLayer from 'features/map/ImageLayer'

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

const getUrl = (layer: string) => {
  return `https://wps-mapserver-dev.apps.silver.devops.gov.bc.ca/cgi-bin/mapserv?map=/etc/mapserver/mapserver.map&MODE=tile&TILEMODE=gmap&LAYERS=${layer}&TILE={x}+{y}+{z}`
  // return `http://localhost:8081/cgi-bin/mapserv?map=/etc/mapserver/mapserver.map&MODE=tile&TILEMODE=gmap&LAYERS=${layer}&TILE={x}+{y}+{z}`
  // return `http://localhost:80/cgi-bin/mapserv?map=/home/sybrand/Workspace/wps/mapserver/sigh.map&MODE=tile&TILEMODE=gmap&LAYERS=${layer}&TILE={x}+{y}+{z}`
}

const ftlSource = new olSource.XYZ({
  url: getUrl('FTL'),
  crossOrigin: 'anonymous',
  // we don't want image smoothing! you can't
  // interpolate between fuel types!
  imageSmoothing: false
})

const easSource = new olSource.XYZ({
  url: getUrl('EAS'),
  // url: getUrl('EAS_WEB_MERCATOR'),
  crossOrigin: 'anonymous',
  // we don't want image smoothing! you can't
  // interpolate if each channel has a different meaning.
  imageSmoothing: false
})

// export function ISIcalc(ffmc: number, ws: number, fbpMod: boolean = false): number {
//   /*
//         #############################################################################
//         # Description:
//         #   Computes the Initial Spread Index From the FWI System. Equations are from
//         #   Van Wagner (1985) as listed below, except for the modification for fbp
//         #   takene from FCFDG (1992).

//         #   Equations and FORTRAN program for the Canadian Forest Fire
//         #   Weather Index System. 1985. Van Wagner, C.E.; Pickett, T.L.
//         #   Canadian Forestry Service, Petawawa National Forestry
//         #   Institute, Chalk River, Ontario. Forestry Technical Report 33.
//         #   18 p.
//         #
//         #   Forestry Canada  Fire Danger Group (FCFDG) (1992). Development and
//         #   Structure of the Canadian Forest Fire Behavior Prediction System."
//         #   Technical ReportST-X-3, Forestry Canada, Ottawa, Ontario.
//         #
//         # Args:
//         #   ffmc:   Fine Fuel Moisture Code
//         #     ws:   Wind Speed (km/h)
//         # fbpMod:   TRUE/FALSE if using the fbp modification at the extreme end
//         #
//         # Returns:
//         #   ISI:    Intial Spread Index
//         #
//         #############################################################################
//         */
//   // #Eq. 10 - Moisture content
//   // fm <- 147.2 * (101 - ffmc)/(59.5 + ffmc)
//   const fm = (147.2 * (101 - ffmc)) / (59.5 + ffmc)
//   // #Eq. 24 - Wind Effect
//   // #the ifelse, also takes care of the ISI modification for the fbp functions
//   // # This modification is Equation 53a in FCFDG (1992)
//   // fW   <- ifelse(ws >= 40 & fbpMod==TRUE,
//   //                12 * (1 - exp(-0.0818 * (ws - 28))),
//   //                exp(0.05039 * ws))
//   const fW =
//     ws >= 40 && fbpMod ? 12 * (1 - Math.exp(-0.0818 * (ws - 28))) : Math.exp(0.05039 * ws)
//   // #Eq. 25 - Fine Fuel Moisture
//   // fF <- 91.9 * exp(-0.1386 * fm) * (1 + (fm^5.31) / 49300000)
//   const fF = 91.9 * Math.exp(-0.1386 * fm) * (1 + Math.pow(fm, 5.31) / 49300000)
//   // #Eq. 26 - Spread Index Equation
//   // isi <- 0.208 * fW * fF
//   return 0.208 * fW * fF
//   // return(isi)
// }

// function calcROSColour(ros: number, opacity: number): number[] {
//   if (ros < 0) {
//     if (ros === -2) {
//       // it's water - or something that doesn't burn.
//       return [0, 0, 0, 0]
//     }
//     // don't know what this is!
//     return [0x0, 0x0, 0x0, opacity]
//   }
//   // return [0xff, 0x00, 0x00, 0xff]
//   if (ros < 3) {
//     // low, green
//     return [0, 128, 0, opacity]
//   } else if (ros < 8) {
//     // moderate, yellow
//     return [255, 255, 0x0, opacity]
//   } else if (ros < 15) {
//     // high, orange
//     return [255, 165, 0, opacity]
//   }
//   // extreme, red
//   return [255, 0, 0, opacity]

//   // gradient:
//   // return [0xff, Math.max(0, 255 - (ros / 100) * 255), 0x00, opacity]
//   // matching redbook:
//   // if (ros <= 0.8) {
//   //   // dark grey
//   //   return [0xa9, 0xa9, 0xa9]
//   // } else if (ros <= 3) {
//   //   return [0xd3, 0xd3, 0xd3]
//   // } else if (ros <= 6) {
//   //   return [0xff, 0xc2, 0xc2]
//   // } else if (ros <= 13) {
//   //   return [0xff, 0x62, 0x00]
//   // }
//   // return [0xff, 0x00, 0x00]
// }

// function ftlNumberToFtlCode(ftlNumber: number): string | undefined {
//   switch (ftlNumber) {
//     case 1:
//       return 'C1'
//     case 2:
//       return 'C2'
//     case 3:
//       return 'C3'
//     case 4:
//       return 'C4'
//     case 5:
//       return 'C5'
//     case 6:
//       // Not sure - but seems logical?
//       return 'C6'
//     case 7:
//       return 'C7'
//     case 11:
//       return 'D1'
//     case 12:
//       return 'D1'
//     case 13:
//       return 'D1'
//   }
//   if (ftlNumber >= 500 && ftlNumber < 700) {
//     return 'M1'
//   }
//   return undefined
// }

// function isNonFuel(ftlNumber: number): boolean {
//   throw new Error('this is here to fool typescript')
// }

// export function ROScalc(
//   FUELTYPE: string,
//   ISI: number,
//   BUI: number,
//   FMC: number,
//   SFC: number | undefined = undefined,
//   PC: number | undefined = undefined,
//   PDF: number | undefined = undefined,
//   CC: number | undefined = undefined,
//   CBH: number
// ): number {
//   const NoBUI = -1
//   const d = [
//     'C1',
//     'C2',
//     'C3',
//     'C4',
//     'C5',
//     'C6',
//     'C7',
//     'D1',
//     'M1',
//     'M2',
//     'M3',
//     'M4',
//     'S1',
//     'S2',
//     'S3',
//     'O1A',
//     'O1B'
//   ]
//   const a = [90, 110, 110, 110, 30, 30, 45, 30, 0, 0, 120, 100, 75, 40, 55, 190, 250]
//   const b = [
//     0.0649,
//     0.0282,
//     0.0444,
//     0.0293,
//     0.0697,
//     0.08,
//     0.0305,
//     0.0232,
//     0,
//     0,
//     0.0572,
//     0.0404,
//     0.0297,
//     0.0438,
//     0.0829,
//     0.031,
//     0.035
//   ]
//   const c0 = [
//     4.5,
//     1.5,
//     3.0,
//     1.5,
//     4.0,
//     3.0,
//     2.0,
//     1.6,
//     0,
//     0,
//     1.4,
//     1.48,
//     1.3,
//     1.7,
//     3.2,
//     1.4,
//     1.7
//   ]

//   const index = d.indexOf(FUELTYPE)

//   let rsi = -1

//   // Eq. 26 (FCFDG 1992) - Initial Rate of Spread for Conifer and Slash types
//   // RSI <- ifelse(FUELTYPE %in% c("C1", "C2", "C3", "C4", "C5", "C7", "D1", "S1",
//   //                               "S2", "S3"),
//   //         as.numeric(a[FUELTYPE] * (1 - exp(-b[FUELTYPE] * ISI))**c0[FUELTYPE]),
//   //         RSI)
//   if (['C1', 'C2', 'C3', 'C4', 'C5', 'C7', 'D1', 'S1', 'S2', 'S3'].includes(FUELTYPE)) {
//     rsi = a[index] * Math.pow(1 - Math.exp(-b[index] * ISI), c0[index])
//   }
//   // #Eq. 27 (FCFDG 1992) - Initial Rate of Spread for M1 Mixedwood type
//   // RSI <- ifelse(FUELTYPE %in% c("M1"),
//   //           PC/100 *
//   //             .ROScalc(rep("C2", length(ISI)),ISI,NoBUI,FMC,SFC,PC,PDF,CC,CBH)
//   //             + (100 - PC) / 100 *
//   //             .ROScalc(rep("D1", length(ISI)),ISI,NoBUI,FMC,SFC,PC,PDF,CC, CBH),
//   //           RSI)
//   else if (FUELTYPE === 'M1') {
//     if (!PC) {
//       throw new Error('PC not specified')
//     }
//     rsi =
//       (PC / 100) * ROScalc('C2', ISI, NoBUI, FMC, SFC, PC, PDF, CC, CBH) +
//       ((100 - PC) / 100) * ROScalc('D1', ISI, NoBUI, FMC, SFC, PC, PDF, CC, CBH)
//   }
//   // #Eq. 27 (FCFDG 1992) - Initial Rate of Spread for M2 Mixedwood type
//   // RSI <- ifelse(FUELTYPE %in% c("M2"),
//   //           PC/100 *
//   //             .ROScalc(rep("C2", length(ISI)),ISI,NoBUI,FMC,SFC,PC,PDF,CC,CBH)
//   //             + 0.2*(100-PC)/100 *
//   //             .ROScalc(rep("D1", length(ISI)),ISI,NoBUI,FMC,SFC,PC,PDF,CC, CBH),
//   //           RSI)
//   else if (FUELTYPE === 'M2') {
//     if (!PC) {
//       throw new Error('PC not specified')
//     }
//     rsi =
//       (PC / 100) * ROScalc('C2', ISI, NoBUI, FMC, SFC, PC, PDF, CC, CBH) +
//       ((0.2 * (100 - PC)) / 100) * ROScalc('D1', ISI, NoBUI, FMC, SFC, PC, PDF, CC, CBH)
//   }

//   // #Initial Rate of Spread for M3 Mixedwood
//   // RSI_m3 <- rep(-99,length(ISI))
//   // #Eq. 30 (Wotton et. al 2009)
//   // RSI_m3 <-
//   //   ifelse(FUELTYPE %in% c("M3"),
//   //     as.numeric(a[["M3"]] * ((1 - exp(-b[["M3"]] * ISI))**c0[["M3"]])), RSI_m3)
//   // #Eq. 29 (Wotton et. al 2009)
//   // RSI <-
//   //   ifelse(FUELTYPE %in% c("M3"),
//   //     PDF/100* RSI_m3 + (1-PDF/100) *
//   //       .ROScalc(rep("D1", length(ISI)), ISI, NoBUI, FMC, SFC, PC, PDF, CC,CBH),
//   //     RSI)
//   else if (FUELTYPE === 'M3') {
//     if (!PDF) {
//       throw new Error('PDF not specified')
//     }
//     const RSI_m3 = a[index] * Math.pow(1 - Math.exp(-b[index] * ISI), c0[index])
//     rsi =
//       (PDF / 100) * RSI_m3 +
//       (1 - PDF / 100) * ROScalc('D1', ISI, NoBUI, FMC, SFC, PC, PDF, CC, CBH)
//   }
//   // #Initial Rate of Spread for M4 Mixedwood
//   // RSI_m4 <- rep(-99,length(ISI))
//   // #Eq. 30 (Wotton et. al 2009)
//   // RSI_m4 <-
//   //   ifelse(FUELTYPE %in% c("M4"),
//   //     as.numeric(a[["M4"]] * ((1 - exp(-b[["M4"]] * ISI))**c0[["M4"]])), RSI_m4)
//   // #Eq. 33 (Wotton et. al 2009)
//   // RSI <-
//   //   ifelse(FUELTYPE %in% c("M4"),
//   //     PDF / 100* RSI_m4 + 0.2 * (1 - PDF / 100)*
//   //       .ROScalc(rep("D1", length(ISI)), ISI, NoBUI, FMC, SFC, PC, PDF, CC,CBH),
//   //     RSI)
//   else if (FUELTYPE === 'M4') {
//     if (!PDF) {
//       throw new Error('PDF not specified')
//     }
//     const RSI_m4 = a[index] * Math.pow(1 - Math.exp(-b[index] * ISI), c0[index])
//     rsi =
//       (PDF / 100) * RSI_m4 +
//       0.2 * (1 - PDF / 100) * ROScalc('D1', ISI, NoBUI, FMC, SFC, PC, PDF, CC, CBH)
//   }
//   // #Eq. 35b (Wotton et. al. 2009) - Calculate Curing function for grass
//   // CF <- rep(-99,length(ISI))
//   // CF <-
//   //   ifelse(FUELTYPE %in% c("O1A", "O1B"),
//   //          ifelse(CC < 58.8,
//   //                 0.005 * (exp(0.061 * CC) - 1),
//   //                 0.176 + 0.02 * (CC - 58.8)),
//   //          CF)
//   // #Eq. 36 (FCFDG 1992) - Calculate Initial Rate of Spread for Grass
//   // RSI <-
//   //   ifelse(FUELTYPE %in% c("O1A", "O1B"),
//   //     a[FUELTYPE] * ((1 - exp(-b[FUELTYPE] * ISI))**c0[FUELTYPE]) * CF,
//   //   RSI)
//   else if (FUELTYPE === 'O1A' || FUELTYPE === 'O1B') {
//     if (!CC) {
//       throw Error('CC not specified')
//     }
//     const CF = CC < 58.8 ? 0.005 * (Math.exp(0.061 * CC) - 1) : 0.176 + 0.02 * (CC - 58.8)
//     rsi = a[index] * Math.pow(1 - Math.exp(-b[index] * ISI), c0[index]) * CF
//   }
//   // #Calculate C6 separately
//   // ROS <-
//   //   ifelse(FUELTYPE %in% c("C6"),
//   //     .C6calc(FUELTYPE, ISI, BUI, FMC, SFC, CBH, option = "ROS"),
//   //     .BEcalc(FUELTYPE, BUI) * RSI)
//   // #add a constraint
//   // ROS <- ifelse(ROS <= 0,0.000001,ROS)
//   let ros: number
//   if (FUELTYPE === 'C6') {
//     ros = C6calc(
//       FUELTYPE,
//       ISI,
//       BUI,
//       FMC,
//       SFC,
//       CBH,
//       undefined,
//       undefined,
//       undefined,
//       'ROS'
//     )
//   } else {
//     ros = BEcalc(FUELTYPE, BUI) * rsi
//   }

//   return ros <= 0 ? 0.000001 : ros
// }

// export function CFBcalc(
//   FUELTYPE: string,
//   FMC: number,
//   SFC: number,
//   ROS: number,
//   CBH: number,
//   option = 'CFB'
// ): number {
//   // .CFBcalc <- function(FUELTYPE, FMC, SFC, ROS, CBH, option="CFB"){
//   //   #############################################################################
//   //   # Description:
//   //   #   Calculate Calculate Crown Fraction Burned. To calculate CFB, we also
//   //   #     need to calculate Critical surface intensity (CSI), and Surface fire
//   //   #     rate of spread (RSO). The value of each of these equations can be
//   //   #     returned to the calling function without unecessary additional
//   //   #     calculations.
//   //   #
//   //   #   All variables names are laid out in the same manner as Forestry Canada
//   //   #   Fire Danger Group (FCFDG) (1992). Development and Structure of the
//   //   #   Canadian Forest Fire Behavior Prediction System." Technical Report
//   //   #   ST-X-3, Forestry Canada, Ottawa, Ontario.
//   //   #
//   //   # Args:
//   //   #   FUELTYPE: The Fire Behaviour Prediction FuelType
//   //   #   FMC:      Foliar Moisture Content
//   //   #   SFC:      Surface Fuel Consumption
//   //   #   CBH:      Crown Base Height
//   //   #   ROS:      Rate of Spread
//   //   #   option:   Which variable to calculate(ROS, CFB, RSC, or RSI)

//   //   # Returns:
//   //   #   CFB, CSI, RSO depending on which option was selected.
//   //   #
//   //   #############################################################################
//   //   CFB <- 0
//   let CFB = 0
//   //   #Eq. 56 (FCFDG 1992) Critical surface intensity
//   //   CSI <- 0.001 * (CBH**1.5) * (460 + 25.9 * FMC)**1.5
//   const CSI = 0.001 * Math.pow(CBH, 1.5) * Math.pow(460 + 25.9 * FMC, 1.5)
//   //   #Return at this point, if specified by caller
//   //   if(option=="CSI"){
//   //     return(CSI)
//   //   }
//   if (option === 'CSI') {
//     return CSI
//   }
//   //   #Eq. 57 (FCFDG 1992) Surface fire rate of spread (m/min)
//   //   RSO <- CSI / (300 * SFC)
//   const RSO = CSI / (300 * SFC)
//   //   #Return at this point, if specified by caller
//   //   if(option=="RSO"){
//   //     return(RSO)
//   //   }
//   if (option === 'RSO') {
//     return RSO
//   }
//   //   #Eq. 58 (FCFDG 1992) Crown fraction burned
//   //   CFB <- ifelse(ROS > RSO, 1 - exp(-0.23 * (ROS - RSO)), CFB)
//   CFB = ROS > RSO ? 1 - Math.exp(-0.23 * (ROS - RSO)) : CFB
//   //   return(CFB)
//   // }
//   return CFB
// }

// export function SFCCalc(
//   FUELTYPE: string,
//   FFMC: number,
//   BUI: number,
//   PC: number,
//   GFL: number | undefined
// ): number {
//   // .SFCcalc <- function(FUELTYPE, FFMC, BUI, PC, GFL) {
//   //   #############################################################################
//   //   # Description:
//   //   #   Computes the Surface Fuel Consumption by Fuel Type.
//   //   #   All variables names are laid out in the same manner as FCFDG (1992) or
//   //   #   Wotton et. al (2009)
//   //   #   Forestry Canada Fire Danger Group (FCFDG) (1992). "Development and
//   //   #   Structure of the Canadian Forest Fire Behavior Prediction System."
//   //   #   Technical Report ST-X-3, Forestry Canada, Ottawa, Ontario.
//   //   #
//   //   #   Wotton, B.M., Alexander, M.E., Taylor, S.W. 2009. Updates and revisions to
//   //   #   the 1992 Canadian forest fire behavior prediction system. Nat. Resour.
//   //   #   Can., Can. For. Serv., Great Lakes For. Cent., Sault Ste. Marie, Ontario,
//   //   #   Canada. Information Report GLC-X-10, 45p.
//   //   #
//   //   # Args:
//   //   #   FUELTYPE: The Fire Behaviour Prediction FuelType
//   //   #        BUI: Buildup Index
//   //   #       FFMC: Fine Fuel Moisture Code
//   //   #         PC: Percent Conifer (%)
//   //   #        GFL: Grass Fuel Load (kg/m^2)
//   //   # Returns:
//   //   #        SFC: Surface Fuel Consumption (kg/m^2)
//   //   #
//   //   #############################################################################
//   //   SFC <- rep(-999,length(FFMC))
//   let SFC = -999
//   //   #Eqs. 9a, 9b (Wotton et. al. 2009) - Solving the lower bound of FFMC value
//   //   # for the C1 fuel type SFC calculation
//   //   SFC <- ifelse(FUELTYPE=="C1",
//   //           ifelse(FFMC > 84,
//   //             0.75 + 0.75 * (1 - exp(-0.23 * (FFMC - 84)))**0.5,
//   //             0.75 - 0.75 * (1 - exp(-0.23 * (84 - FFMC)))**0.5),
//   //           SFC)
//   if (FUELTYPE === 'C1') {
//     SFC =
//       FFMC > 84
//         ? 0.75 + 0.75 * Math.pow(1 - Math.exp(-0.23 * (FFMC - 84)), 0.5)
//         : 0.75 - 0.75 * Math.pow(1 - Math.exp(-0.23 * (84 - FFMC)), 0.5)
//   }
//   //   #Eq. 10 (FCFDG 1992) - C2, M3, and M4 Fuel Types
//   //   SFC <- ifelse(FUELTYPE == "C2" | FUELTYPE == "M3" | FUELTYPE == "M4",
//   //           5.0 * (1 - exp(-0.0115 * BUI)),
//   //           SFC)
//   else if (FUELTYPE === 'C2' || FUELTYPE === 'M3' || FUELTYPE === 'M4') {
//     SFC = 5.0 * (1 - Math.exp(-0.0115 * BUI))
//   }
//   //   #Eq. 11 (FCFDG 1992) - C3, C4 Fuel Types
//   //   SFC <- ifelse(FUELTYPE == "C3" | FUELTYPE == "C4",
//   //           5.0 * (1 - exp(-0.0164 * BUI))**2.24,
//   //           SFC)
//   else if (FUELTYPE === 'C3' || FUELTYPE === 'C4') {
//     SFC = 5.0 * (1 - Math.exp(-0.0164 * BUI)) ** 2.24
//   }
//   //   #Eq. 12 (FCFDG 1992) - C5, C6 Fuel Types
//   //   SFC <- ifelse(FUELTYPE == "C5" | FUELTYPE == "C6",
//   //           5.0 * (1 - exp(-0.0149 * BUI))**2.48,
//   //           SFC)
//   else if (FUELTYPE === 'C5' || FUELTYPE === 'C6') {
//     SFC = 5.0 * (1 - Math.exp(-0.0149 * BUI)) ** 2.48
//   }
//   //   #Eqs. 13, 14, 15 (FCFDG 1992) - C7 Fuel Types
//   // SFC <- ifelse(FUELTYPE == "C7",
//   //         ifelse(FFMC > 70, 2 * (1 - exp(-0.104 * (FFMC - 70))),
//   //           0) + 1.5 * (1 - exp(-0.0201 * BUI)),
//   //         SFC)
//   else if (FUELTYPE === 'C7') {
//     const tmp = FFMC > 70 ? 2 * (1 - Math.exp(-0.104 * (FFMC - 70))) : 0
//     SFC = tmp + 1.5 * (1 - Math.exp(-0.0201 * BUI))
//   }
//   //   #Eq. 16 (FCFDG 1992) - D1 Fuel Type
//   //   SFC <- ifelse(FUELTYPE == "D1", 1.5 * (1 - exp(-0.0183 * BUI)), SFC)
//   else if (FUELTYPE === 'D1') {
//     SFC = 1.5 * (1 - Math.exp(-0.0183 * BUI))
//   }
//   //   #Eq. 17 (FCFDG 1992) - M1 and M2 Fuel Types
//   //   SFC <- ifelse(FUELTYPE == "M1" | FUELTYPE == "M2",
//   //           PC / 100 * (5.0 * (1 - exp(-0.0115 * BUI))) +
//   //            ((100 - PC) / 100 * (1.5 * (1 - exp(-0.0183 * BUI)))),
//   //           SFC)
//   else if (FUELTYPE === 'M1' || FUELTYPE === 'M2') {
//     SFC =
//       (PC / 100) * (5.0 * (1 - Math.exp(-0.0115 * BUI))) +
//       ((100 - PC) / 100) * (1.5 * (1 - Math.exp(-0.0183 * BUI)))
//   }
//   //   #Eq. 18 (FCFDG 1992) - Grass Fuel Types
//   //   SFC <- ifelse(FUELTYPE == "O1A" | FUELTYPE == "O1B", GFL, SFC)
//   else if (FUELTYPE === 'O1A' || FUELTYPE === 'O1B') {
//     if (!GFL) {
//       throw new Error('GFL not provided')
//     }
//     SFC = GFL
//   }
//   //   #Eq. 19, 20, 25 (FCFDG 1992) - S1 Fuel Type
//   //   SFC <- ifelse(FUELTYPE == "S1",
//   //           4.0 * (1 - exp(-0.025 * BUI)) + 4.0 * (1 - exp(-0.034 * BUI)),
//   //           SFC)
//   else if (FUELTYPE === 'S1') {
//     SFC = 4.0 * (1 - Math.exp(-0.025 * BUI)) + 4.0 * (1 - Math.exp(-0.034 * BUI))
//   }
//   //   #Eq. 21, 22, 25 (FCFDG 1992) - S2 Fuel Type
//   //   SFC <- ifelse(FUELTYPE == "S2",
//   //           10.0 * (1 - exp(-0.013 * BUI)) + 6.0 * (1 - exp(-0.060 * BUI)),
//   //           SFC)
//   else if (FUELTYPE === 'S2') {
//     SFC = 10.0 * (1 - Math.exp(-0.013 * BUI)) + 6.0 * (1 - Math.exp(-0.06 * BUI))
//   }
//   //   #Eq. 23, 24, 25 (FCFDG 1992) - S3 Fuel Type
//   //   SFC <- ifelse(FUELTYPE == "S3",
//   //           12.0 * (1 - exp(-0.0166 * BUI)) + 20.0 * (1-exp(-0.0210 * BUI)),
//   //           SFC)
//   else if (FUELTYPE === 'S3') {
//     SFC = 12.0 * (1 - Math.exp(-0.0166 * BUI)) + 20.0 * (1 - Math.exp(-0.021 * BUI))
//   }
//   //   #Constrain SFC value
//   //   SFC <- ifelse(SFC <= 0, 0.000001, SFC)
//   //   return(SFC)
//   // }
//   return SFC <= 0 ? 0.000001 : SFC
// }

// export function Slopecalc(
//   FUELTYPE: string,
//   FFMC: number,
//   BUI: number,
//   WS: number,
//   WAZ: number,
//   GS: number,
//   SAZ: number,
//   FMC: number,
//   SFC: number | undefined,
//   PC: number,
//   PDF: number | undefined,
//   CC: number | undefined,
//   CBH: number,
//   ISI: number | undefined,
//   output: string = 'RAZ'
// ): number {
//   // .Slopecalc <- function(FUELTYPE, FFMC, BUI, WS, WAZ, GS, SAZ, FMC, SFC, PC, PDF,
//   //   CC, CBH, ISI, output = "RAZ") {
//   //   # output options include: RAZ and WSV
//   //   #############################################################################
//   //   # Description:
//   //   #   Calculate the net effective windspeed (WSV), the net effective wind
//   //   #   direction (RAZ) or the wind azimuth (WAZ).
//   //   #
//   //   #   All variables names are laid out in the same manner as FCFDG (1992) and
//   //   #   Wotton (2009).
//   //   #
//   //   #
//   //   #   Forestry Canada Fire Danger Group (FCFDG) (1992). "Development and
//   //   #   Structure of the Canadian Forest Fire Behavior Prediction System."
//   //   #   Technical Report ST-X-3, Forestry Canada, Ottawa, Ontario.
//   //   #
//   //   #   Wotton, B.M., Alexander, M.E., Taylor, S.W. 2009. Updates and revisions to
//   //   #   the 1992 Canadian forest fire behavior prediction system. Nat. Resour.
//   //   #   Can., Can. For. Serv., Great Lakes For. Cent., Sault Ste. Marie, Ontario,
//   //   #   Canada. Information Report GLC-X-10, 45p.
//   //   #
//   //   # Args:
//   //   #   FUELTYPE: The Fire Behaviour Prediction FuelType
//   //   #       FFMC: Fine Fuel Moisture Code
//   //   #        BUI: The Buildup Index value
//   //   #         WS: Windspeed (km/h)
//   //   #        WAZ: Wind Azimuth
//   //   #         GS: Ground Slope (%)
//   //   #        SAZ: Slope Azimuth
//   //   #        FMC: Foliar Moisture Content
//   //   #        SFC: Surface Fuel Consumption (kg/m^2)
//   //   #         PC: Percent Conifer (%)
//   //   #        PDF: Percent Dead Balsam Fir (%)
//   //   #         CC: Constant
//   //   #        CBH: Crown Base Height (m)
//   //   #        ISI: Initial Spread Index
//   //   #     output: Type of variable to output (RAZ/WSV, default=RAZ)
//   //   # Returns:
//   //   #   BE: The Buildup Effect
//   //   #
//   //   #############################################################################
//   //   #check for valid output types
//   //   validOutTypes = c("RAZ", "WAZ", "WSV")
//   //   if(!(output %in% validOutTypes)){
//   //   stop(paste("In 'slopecalc()', '",output, "' is an invalid 'output' type.",
//   //   sep=""))
//   //   }
//   if (!['RAZ', 'WAZ', 'WSV'].includes(output)) {
//     throw Error("In 'slopecalc()', '" + output + "' is an invalid 'output' type.")
//   }
//   //   NoBUI <- rep(-1,length(FFMC))
//   const NoBUI = -1
//   //   #Eq. 39 (FCFDG 1992) - Calculate Spread Factor
//   //   SF <- ifelse (GS >= 70, 10, exp(3.533 * (GS / 100)^1.2))
//   const SF = GS >= 70 ? 10 : Math.exp(3.533 * Math.pow(GS / 100, 1.2))
//   //   #ISI with 0 wind on level grounds
//   //   ISZ <- .ISIcalc(FFMC, 0)
//   const ISZ = ISIcalc(FFMC, 0)
//   //   #Surface spread rate with 0 wind on level ground
//   //   RSZ <- .ROScalc(FUELTYPE, ISZ, BUI = NoBUI, FMC, SFC, PC, PDF, CC, CBH)
//   let RSZ = ROScalc(FUELTYPE, ISZ, NoBUI, FMC, SFC, PC, PDF, CC, CBH)
//   //   #Eq. 40 (FCFDG 1992) - Surface spread rate with 0 wind upslope
//   //   RSF <- RSZ * SF
//   const RSF = RSZ * SF
//   //   #setup some reference vectors
//   //   d <- c("C1", "C2", "C3", "C4", "C5", "C6", "C7", "D1", "M1", "M2", "M3", "M4",
//   //   "S1", "S2", "S3", "O1A", "O1B")
//   const d = [
//     'C1',
//     'C2',
//     'C3',
//     'C4',
//     'C5',
//     'C6',
//     'C7',
//     'D1',
//     'M1',
//     'M2',
//     'M3',
//     'M4',
//     'S1',
//     'S2',
//     'S3',
//     'O1A',
//     'O1B'
//   ]
//   const index = d.indexOf(FUELTYPE)
//   const c2_index = d.indexOf('C2')
//   const d1_index = d.indexOf('D1')
//   //   a <- c(90, 110, 110, 110, 30, 30, 45, 30, 0, 0, 120, 100, 75, 40, 55, 190,
//   //   250)
//   const a = [90, 110, 110, 110, 30, 30, 45, 30, 0, 0, 120, 100, 75, 40, 55, 190, 250]
//   //   b <- c(0.0649, 0.0282, 0.0444, 0.0293, 0.0697, 0.0800, 0.0305, 0.0232, 0, 0,
//   //   0.0572, 0.0404, 0.0297, 0.0438, 0.0829, 0.0310, 0.0350)
//   const b = [
//     0.0649,
//     0.0282,
//     0.0444,
//     0.0293,
//     0.0697,
//     0.08,
//     0.0305,
//     0.0232,
//     0,
//     0,
//     0.0572,
//     0.0404,
//     0.0297,
//     0.0438,
//     0.0829,
//     0.031,
//     0.035
//   ]
//   //   c0 <- c(4.5, 1.5, 3.0, 1.5, 4.0, 3.0, 2.0, 1.6, 0, 0, 1.4, 1.48, 1.3, 1.7,
//   //   3.2, 1.4, 1.7)
//   const c0 = [
//     4.5,
//     1.5,
//     3.0,
//     1.5,
//     4.0,
//     3.0,
//     2.0,
//     1.6,
//     0,
//     0,
//     1.4,
//     1.48,
//     1.3,
//     1.7,
//     3.2,
//     1.4,
//     1.7
//   ]
//   //   names(a) <- names(b) <- names(c0) <- d

//   //   #initialize some local vars
//   //   RSZ <- rep(-99,length(FFMC))
//   RSZ = -99
//   //   RSF_C2 <- rep(-99,length(FFMC))
//   //   RSF_D1 <- rep(-99,length(FFMC))
//   //   RSF_M3 <- rep(-99,length(FFMC))
//   //   RSF_M4 <- rep(-99,length(FFMC))
//   //   CF <- rep(-99,length(FFMC))
//   //   ISF <- rep(-99,length(FFMC))
//   let ISF = -99
//   //   ISF_C2 <- rep(-99,length(FFMC))
//   //   ISF_D1 <- rep(-99,length(FFMC))
//   //   ISF_M3 <- rep(-99,length(FFMC))
//   //   ISF_M4 <- rep(-99,length(FFMC))

//   //   #Eqs. 41a, 41b (Wotton 2009) - Calculate the slope equivalend ISI
//   //   ISF <- ifelse(FUELTYPE %in% c("C1", "C2", "C3", "C4", "C5", "C6", "C7", "D1",
//   //               "S1", "S2", "S3"),
//   //   ifelse((1 - (RSF / a[FUELTYPE])**(1 / c0[FUELTYPE])) >= 0.01,
//   //   log(1 - (RSF / a[FUELTYPE])**(1 / c0[FUELTYPE])) / (-b[FUELTYPE]),
//   //   log(0.01)/(-b[FUELTYPE])),
//   //   ISF)
//   if (
//     ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'D1', 'S1', 'S2', 'S3'].includes(FUELTYPE)
//   ) {
//     ISF =
//       1 - Math.pow(RSF / a[index], 1 / c0[index]) >= 0.01
//         ? Math.log(1 - Math.pow(RSF / a[index], 1 / c0[index])) / -b[index]
//         : Math.log(0.01) / -b[index]
//   }
//   //   #When calculating the M1/M2 types, we are going to calculate for both C2
//   //   # and D1 types, and combine
//   //   #Surface spread rate with 0 wind on level ground
//   else if (['M1', 'M2'].includes(FUELTYPE)) {
//     // RSZ <- ifelse(FUELTYPE %in% c("M1", "M2"),
//     //        .ROScalc(rep("C2", length(ISZ)), ISZ, BUI = NoBUI, FMC, SFC, PC, PDF,
//     //                 CC, CBH),
//     //        RSZ)
//     let RSZ = ROScalc('C2', ISZ, NoBUI, FMC, SFC, PC, PDF, CC, CBH)
//     // #Eq. 40 (FCFDG 1992) - Surface spread rate with 0 wind upslope for C2
//     // RSF_C2 <- ifelse(FUELTYPE %in% c("M1", "M2"), RSZ * SF, RSF_C2)
//     const RSF_C2 = RSZ * SF
//     // RSZ <- ifelse(FUELTYPE %in% c("M1", "M2"),
//     //         .ROScalc(rep("D1", length(ISZ)), ISZ, BUI = NoBUI, FMC, SFC, PC,
//     //                   PDF, CC, CBH),RSZ)
//     RSZ = ROScalc('D1', ISZ, NoBUI, FMC, SFC, PC, PDF, CC, CBH)
//     // #Eq. 40 (FCFDG 1992) - Surface spread rate with 0 wind upslope for D1
//     // RSF_D1 <- ifelse(FUELTYPE %in% c("M1", "M2"), RSZ * SF, RSF_D1)
//     // RSF0 <- 1 - (RSF_C2 / a[["C2"]])^(1 / c0[["C2"]])
//     const RSF_D1 = RSZ * SF
//     let RSF0 = 1 - Math.pow(RSF_C2 / a[c2_index], 1 / c0[c2_index])
//     // #Eq. 41a (Wotton 2009) - Calculate the slope equivalent ISI
//     // ISF_C2 <- ifelse(FUELTYPE %in% c("M1", "M2") & RSF0 >= 0.01,
//     //             log(1 - (RSF_C2 / a[["C2"]])**(1 / c0[["C2"]])) / (-b[["C2"]]),
//     //             ISF_C2)
//     // #Eq. 41b (Wotton 2009) - Calculate the slope equivalent ISI
//     // ISF_C2 <- ifelse(FUELTYPE %in% c("M1", "M2") & RSF0 < 0.01,
//     //             log(0.01) / (-b[["C2"]]),
//     //             ISF_C2)
//     const ISF_C2 =
//       RSF0 >= 0.01
//         ? Math.log(1 - Math.pow(RSF_C2 / a[c2_index], 1 / c0[c2_index])) / -b[c2_index]
//         : Math.log(0.01) / -b[c2_index]
//     // RSF0 <- 1 - (RSF_D1 / a[["D1"]])^(1 / c0[["D1"]])
//     RSF0 = (1 - RSF_D1 / a[d1_index]) ^ (1 / c0[d1_index])
//     // #Eq. 41a (Wotton 2009) - Calculate the slope equivalent ISI
//     // ISF_D1 <- ifelse(FUELTYPE %in% c("M1", "M2") & RSF0 >= 0.01,
//     //             log(1 - (RSF_D1 / a[["D1"]])**(1 / c0[["D1"]])) / (-b[["D1"]]),
//     //             ISF_D1)
//     // #Eq. 41b (Wotton 2009) - Calculate the slope equivalent ISI
//     // ISF_D1 <- ifelse(FUELTYPE %in% c("M1", "M2") & RSF0 < 0.01,
//     //             log(0.01) / (-b[["D1"]]),
//     //             ISF_D1)
//     const ISF_D1 =
//       RSF0 >= 0.01
//         ? Math.log(1 - Math.pow(RSF_D1 / a[d1_index], 1 / c0[d1_index])) / -b[d1_index]
//         : Math.log(0.01) / -b[d1_index]
//     // #Eq. 42a (Wotton 2009) - Calculate weighted average for the M1/M2 types
//     // ISF <- ifelse(FUELTYPE %in% c("M1", "M2"), PC / 100 * ISF_C2 +
//     //                 (1 - PC / 100) * ISF_D1,
//     //               ISF)
//     ISF = (PC / 100) * ISF_C2 + (1 - PC / 100) * ISF_D1
//   } else if (FUELTYPE === 'M3') {
//     //   #Set % Dead Balsam Fir to 100%
//     //   PDF100 <- rep(100, length(ISI))
//     //   #Surface spread rate with 0 wind on level ground
//     //   RSZ <- ifelse(FUELTYPE %in% c("M3"),
//     //   .ROScalc(rep("M3", length(FMC)), ISI = ISZ, BUI = NoBUI, FMC, SFC,
//     //   PC, PDF100, CC, CBH),
//     //   RSZ)
//     //   #Eq. 40 (FCFDG 1992) - Surface spread rate with 0 wind upslope for M3
//     //   RSF_M3 <- ifelse(FUELTYPE %in% c("M3"), RSZ * SF, RSF_M3)
//     //   #Surface spread rate with 0 wind on level ground, using D1
//     //   RSZ <- ifelse(FUELTYPE %in% c("M3"),
//     //   .ROScalc(rep("D1", length(ISZ)), ISZ, BUI = NoBUI, FMC, SFC, PC,
//     //   PDF100, CC, CBH),
//     //   RSZ)
//     //   #Eq. 40 (FCFDG 1992) - Surface spread rate with 0 wind upslope for M3
//     //   RSF_D1 <- ifelse(FUELTYPE %in% c("M3"), RSZ * SF, RSF_D1)
//     //   RSF0 <- 1 - (RSF_M3 / a[["M3"]])^(1 / c0[["M3"]])
//     //   #Eq. 41a (Wotton 2009) - Calculate the slope equivalent ISI
//     //   ISF_M3 <- ifelse(FUELTYPE %in% c("M3") & RSF0 >= 0.01,
//     //   log(1 - (RSF_M3/a[["M3"]])**(1/c0[["M3"]]))/(-b[["M3"]]),ISF_M3)
//     //   #Eq. 41b (Wotton 2009) - Calculate the slope equivalent ISI
//     //   ISF_M3 <- ifelse(FUELTYPE %in% c("M3") & RSF0 < 0.01,
//     //   log(0.01) / (-b[["M3"]]),
//     //   ISF_M3)
//     //   #Eq. 40 (FCFDG 1992) - Surface spread rate with 0 wind upslope for D1
//     //   RSF0 <- 1 - (RSF_D1 / a[["D1"]])^(1 / c0[["D1"]])
//     //   #Eq. 41a (Wotton 2009) - Calculate the slope equivalent ISI
//     //   ISF_D1 <- ifelse(FUELTYPE %in% c("M3") & RSF0 >= 0.01,
//     //   log(1 - (RSF_D1 / a[["D1"]])**(1 / c0[["D1"]])) / (-b[["D1"]]),
//     //   ISF_D1)
//     //   #Eq. 41b (Wotton 2009) - Calculate the slope equivalent ISI
//     //   ISF_D1 <- ifelse(FUELTYPE %in% c("M3") & RSF0 < 0.01,
//     //   log(0.01) / (-b[["D1"]]),
//     //   ISF_D1)
//     //   #Eq. 42b (Wotton 2009) - Calculate weighted average for the M3 type
//     //   ISF <- ifelse(FUELTYPE %in% c("M3"),
//     //   PDF / 100 * ISF_M3 + (1 - PDF / 100) * ISF_D1,
//     //   ISF)
//     throw Error('slope for M3 not implemented')
//   }
//   //   #Surface spread rate with 0 wind on level ground, using M4
//   else if (FUELTYPE === 'M4') {
//     //   RSZ <- ifelse(FUELTYPE %in% c("M4"),
//     //   .ROScalc(rep("M4", length(FMC)), ISI = ISZ, BUI = NoBUI, FMC, SFC,
//     //   PC, PDF100, CC, CBH),
//     //   RSZ)
//     //   #Eq. 40 (FCFDG 1992) - Surface spread rate with 0 wind upslope for M4
//     //   RSF_M4 <- ifelse(FUELTYPE %in% c("M4"), RSZ * SF, RSF_M4)
//     //   #Surface spread rate with 0 wind on level ground, using M4
//     //   RSZ <- ifelse(FUELTYPE %in% c("M4"),
//     //   .ROScalc(rep("D1", length(ISZ)), ISZ, BUI = NoBUI, FMC, SFC, PC,
//     //   PDF100, CC, CBH),
//     //   RSZ)
//     //   #Eq. 40 (FCFDG 1992) - Surface spread rate with 0 wind upslope for D1
//     //   RSF_D1 <- ifelse(FUELTYPE %in% c("M4"), RSZ * SF,RSF_D1)
//     //   #Eq. 40 (FCFDG 1992) - Surface spread rate with 0 wind upslope for D1
//     //   RSF0 <- 1 - (RSF_M4 / a[["M4"]])^(1 / c0[["M4"]])
//     //   #Eq. 41a (Wotton 2009) - Calculate the slope equivalent ISI
//     //   ISF_M4 <- ifelse(FUELTYPE %in% c("M4") & RSF0 >= 0.01,
//     //   log(1 - (RSF_M4 / a[["M4"]])**(1 / c0[["M4"]])) / (-b[["M4"]]),
//     //   ISF_M4)
//     //   #Eq. 41b (Wotton 2009) - Calculate the slope equivalent ISI
//     //   ISF_M4 <- ifelse(FUELTYPE %in% c("M4") & RSF0 < 0.01,
//     //   log(0.01) / (-b[["M4"]]),
//     //   ISF_M4)
//     //   #Eq. 40 (FCFDG 1992) - Surface spread rate with 0 wind upslope for D1
//     //   RSF0 <- 1 - (RSF_D1 / a[["D1"]])^(1 / c0[["D1"]])
//     //   #Eq. 41a (Wotton 2009) - Calculate the slope equivalent ISI (D1)
//     //   ISF_D1 <- ifelse(FUELTYPE %in% c("M4") & RSF0 >= 0.01,
//     //   log(1 - (RSF_D1 / a[["D1"]])**(1 / c0[["D1"]])) / (-b[["D1"]]),
//     //   ISF_D1)
//     //   #Eq. 41b (Wotton 2009) - Calculate the slope equivalent ISI (D1)
//     //   ISF_D1 <- ifelse(FUELTYPE %in% c("M4") & RSF0 < 0.01,
//     //   log(0.01) / (-b[["D1"]]),
//     //   ISF_D1)
//     //   #Eq. 42c (Wotton 2009) - Calculate weighted average for the M4 type
//     //   ISF <- ifelse(FUELTYPE %in% c("M4"), PDF / 100 * ISF_M4 + (1 - PDF / 100.) *
//     //   ISF_D1,
//     //   ISF)
//     throw Error('slope for M4 not implemented')
//   }
//   //   #Eqs. 35a, 35b (Wotton 2009) - Curing Factor pivoting around % 58.8
//   else if (['O1A', 'O1B'].includes(FUELTYPE)) {
//     //   CF <- ifelse(FUELTYPE %in% c("O1A", "O1B"),
//     //   ifelse(CC < 58.8, 0.005 * (exp(0.061 * CC) - 1),
//     //   0.176 + 0.02 * (CC-58.8)),
//     //   CF)
//     //   #Eqs. 43a, 43b (Wotton 2009) - slope equivilent ISI for Grass
//     //   ISF <- ifelse(FUELTYPE %in% c("O1A", "O1B"),
//     //   ifelse((1 - (RSF / (CF * a[FUELTYPE]))**(1 / c0[FUELTYPE])) >= 0.01,
//     //   log(1 - (RSF / (CF * a[FUELTYPE]))**(1 / c0[FUELTYPE])) /
//     //   (-b[FUELTYPE]),
//     //   log(0.01) / (-b[FUELTYPE])),
//     //   ISF)
//     throw Error('slope for O1A, O1b not implemented')
//   }
//   //   #Eq. 46 (FCFDG 1992)
//   //   m <- 147.2 * (101 - FFMC) / (59.5 + FFMC)
//   const m = (147.2 * (101 - FFMC)) / (59.5 + FFMC)
//   //   #Eq. 45 (FCFDG 1992) - FFMC function from the ISI equation
//   //   fF <- 91.9 * exp(-.1386 * m) * (1 + (m**5.31) / 4.93e7)
//   const fF = 91.9 * Math.exp(-0.1386 * m) * (1 + Math.pow(m, 5.31) / 4.93e7)
//   //   #Eqs. 44a, 44d (Wotton 2009) - Slope equivalent wind speed
//   //   WSE <- 1 / 0.05039 * log(ISF / (0.208 * fF))
//   let WSE = (1 / 0.05039) * Math.log(ISF / (0.208 * fF))
//   //   #Eqs. 44b, 44e (Wotton 2009) - Slope equivalent wind speed
//   //   WSE <- ifelse(WSE > 40 & ISF < (0.999 * 2.496 * fF),
//   //   28 - (1 / 0.0818 * log(1 - ISF/ ( 2.496 * fF))),
//   //   WSE)
//   WSE =
//     WSE > 40 && ISF < 0.999 * 2.496 * fF
//       ? 28 - (1 / 0.0818) * Math.log(1 - ISF / (2.496 * fF))
//       : WSE
//   //   #Eqs. 44c (Wotton 2009) - Slope equivalent wind speed
//   //   WSE <- ifelse(WSE > 40 & ISF >= (0.999 * 2.496 * fF), 112.45, WSE)
//   WSE = WSE > 40 && ISF >= 0.999 * 2.496 * fF ? 112.45 : WSE
//   //   #Eq. 47 (FCFDG 1992) - resultant vector magnitude in the x-direction
//   //   WSX <- WS * sin(WAZ) + WSE * sin(SAZ)
//   const WSX = WS * Math.sin(WAZ) + WSE * Math.sin(SAZ)
//   //   #Eq. 48 (FCFDG 1992) - resultant vector magnitude in the y-direction
//   //   WSY <- WS * cos(WAZ) + WSE * cos(SAZ)
//   const WSY = WS * Math.cos(WAZ) + WSE * Math.cos(SAZ)
//   //   #Eq. 49 (FCFDG 1992) - the net effective wind speed
//   //   WSV <- sqrt(WSX * WSX + WSY * WSY)
//   const WSV = Math.sqrt(WSX * WSX + WSY * WSY)
//   //   #stop execution here and return WSV if requested
//   //   if (output=="WSV")
//   //   return(WSV)
//   if (output === 'WSV') {
//     return WSV
//   }
//   //   #Eq. 50 (FCFDG 1992) - the net effective wind direction (radians)
//   //   RAZ <- acos(WSY / WSV)
//   let RAZ = Math.acos(WSY / WSV)
//   //   #Eq. 51 (FCFDG 1992) - convert possible negative RAZ into more understandable
//   //   # directions
//   //   RAZ <- ifelse(WSX < 0, 2 * pi - RAZ, RAZ)
//   RAZ = WSX < 0 ? 2 * Math.PI - RAZ : RAZ
//   //   return(RAZ)
//   return RAZ
// }

// export function C6calc(
//   FUELTYPE: string,
//   ISI: number,
//   BUI: number,
//   FMC: number,
//   SFC: number | undefined,
//   CBH: number | undefined,
//   ROS: number | undefined,
//   CFB: number | undefined,
//   RSC: number | undefined,
//   option: string = 'CFB'
// ): number {
//   //     .C6calc<-function(FUELTYPE, ISI, BUI, FMC, SFC, CBH, ROS, CFB, RSC,
//   //       option="CFB"){
//   // #############################################################################
//   // # Description:
//   // #   Calculate c6 (Conifer plantation) Fire Spread. C6 is a special case, and
//   // #     thus has it's own function. To calculate C6 fire spread, this function
//   // #     also calculates and can return ROS, CFB, RSC, or RSI by specifying in
//   // #     the option parameter.
//   // #
//   // #   All variables names are laid out in the same manner as Forestry Canada
//   // #   Fire Danger Group (FCFDG) (1992). Development and Structure of the
//   // #   Canadian Forest Fire Behavior Prediction System." Technical Report
//   // #   ST-X-3, Forestry Canada, Ottawa, Ontario.
//   // #
//   // # Args:
//   // #   FUELTYPE: The Fire Behaviour Prediction FuelType
//   // #   ISI:      Initial Spread Index
//   // #   BUI:      Buildup Index
//   // #   FMC:      Foliar Moisture Content
//   // #   SFC:      Surface Fuel Consumption
//   // #   CBH:      Crown Base Height
//   // #   ROS:      Rate of Spread
//   // #   CFB:      Crown Fraction Burned
//   // #   RSC:      Crown Fire Spread Rate (m/min)
//   // #   option:   Which variable to calculate(ROS, CFB, RSC, or RSI)
//   // #
//   // # Returns:
//   // #   ROS, CFB, RSC or RSI depending on which option was selected
//   // #
//   // #############################################################################
//   // #Average foliar moisture effect
//   // FMEavg <- 0.778
//   const FMEavg = 0.778
//   // #Eq. 59 (FCFDG 1992) Crown flame temperature (degrees K)
//   // tt <- 1500 - 2.75 * FMC
//   // const tt = 1500 - 2.75 * FMC
//   // #Eq. 60 (FCFDG 1992) Head of ignition (kJ/kg)
//   // H <- 460 + 25.9 * FMC
//   // const H = 460 + 25.9 * FMC
//   // #Eq. 61 (FCFDG 1992) Average foliar moisture effect
//   // FME <- ((1.5 - 0.00275 * FMC)**4.)/(460 + 25.9 * FMC) * 1000
//   const FME = (Math.pow(1.5 - 0.00275 * FMC, 4.0) / (460 + 25.9 * FMC)) * 1000
//   // #Eq. 62 (FCFDG 1992) Intermediate surface fire spread rate
//   // RSI <- 30 * (1 - exp(-0.08 * ISI))**3.0
//   const RSI = 30 * Math.pow(1 - Math.exp(-0.08 * ISI), 3.0)
//   // #Return at this point, if specified by caller
//   // if(option=="RSI"){
//   // return(RSI)
//   // }
//   if (option === 'RSI') {
//     return RSI
//   }
//   // #Eq. 63 (FCFDG 1992) Surface fire spread rate (m/min)
//   // RSS <- RSI * .BEcalc(FUELTYPE, BUI)
//   const RSS = RSI * BEcalc(FUELTYPE, BUI)
//   // #Eq. 64 (FCFDG 1992) Crown fire spread rate (m/min)
//   // RSC <- 60 * (1 - exp(-0.0497 * ISI)) * FME / FMEavg
//   RSC = (60 * (1 - Math.exp(-0.0497 * ISI)) * FME) / FMEavg
//   // #Return at this point, if specified by caller
//   // if(option=="RSC"){
//   // return(RSC)
//   // }
//   if (option === 'RSC') {
//     return RSC
//   }
//   // #Crown Fraction Burned
//   // CFB    <- ifelse(RSC > RSS,.CFBcalc(FUELTYPE, FMC, SFC, RSS, CBH),0)
//   if (!SFC) {
//     throw new Error('SFC not specified')
//   }
//   if (!CBH) {
//     throw new Error('CBH not specified')
//   }
//   CFB = RSC > RSS ? CFBcalc(FUELTYPE, FMC, SFC, RSS, CBH) : 0
//   // #Return at this point, if specified by caller
//   // if(option=="CFB"){
//   // return(CFB)
//   // }
//   if (option === 'CFB') {
//     return CFB
//   }
//   // #Eq. 65 (FCFDG 1992) Calculate Rate of spread (m/min)
//   // ROS    <- ifelse(RSC > RSS,RSS + (CFB)*(RSC-RSS),RSS)
//   // return(ROS)
//   // }
//   return RSC > RSS ? RSS + CFB * (RSC - RSS) : RSS
// }

// export function BEcalc(FUELTYPE: string, BUI: number): number {
//   // #############################################################################
//   // # Description:
//   // #   Computes the Buildup Effect on Fire Spread Rate.
//   // #
//   // #   All variables names are laid out in the same manner as Forestry Canada
//   // #   Fire Danger Group (FCFDG) (1992). Development and Structure of the
//   // #   Canadian Forest Fire Behavior Prediction System." Technical Report
//   // #   ST-X-3, Forestry Canada, Ottawa, Ontario.
//   // #
//   // # Args:
//   // #   FUELTYPE: The Fire Behaviour Prediction FuelType
//   // #   BUI:      The Buildup Index value
//   // # Returns:
//   // #   BE: The Buildup Effect
//   // #
//   // #############################################################################
//   // #Fuel Type String represenations
//   // d <- c("C1", "C2", "C3", "C4", "C5", "C6", "C7", "D1", "M1", "M2", "M3",
//   //        "M4","S1", "S2", "S3", "O1A", "O1B")
//   const d = [
//     'C1',
//     'C2',
//     'C3',
//     'C4',
//     'C5',
//     'C6',
//     'C7',
//     'D1',
//     'M1',
//     'M2',
//     'M3',
//     'M4',
//     'S1',
//     'S2',
//     'S3',
//     'O1A',
//     'O1B'
//   ]
//   // #The average BUI for the fuel type - as referenced by the "d" list above
//   // BUIo <- c(72, 64, 62, 66, 56, 62, 106, 32, 50, 50, 50, 50, 38, 63, 31, 01,
//   //           01)
//   const BUIo = [72, 64, 62, 66, 56, 62, 106, 32, 50, 50, 50, 50, 38, 63, 31, 1, 1]
//   // #Proportion of maximum possible spread rate that is reached at a standard BUI
//   // Q <- c(0.9, 0.7, 0.75, 0.8, 0.8, 0.8, 0.85, 0.9, 0.8, 0.8, 0.8, 0.8, 0.75,
//   //        0.75, 0.75, 1.0, 1.0)
//   const Q = [
//     0.9,
//     0.7,
//     0.75,
//     0.8,
//     0.8,
//     0.8,
//     0.85,
//     0.9,
//     0.8,
//     0.8,
//     0.8,
//     0.8,
//     0.75,
//     0.75,
//     0.75,
//     1.0,
//     1.0
//   ]
//   // names(BUIo) <- names(Q)<-d
//   const index = d.indexOf(FUELTYPE)

//   // #Eq. 54 (FCFDG 1992) The Buildup Effect
//   // BE<- ifelse(BUI > 0 & BUIo[FUELTYPE] > 0,
//   //   exp(50 * log(Q[FUELTYPE]) * (1 / BUI - 1 / BUIo[FUELTYPE])), 1)
//   // return(as.numeric(BE))
//   return BUI > 0 && BUIo[index] > 0
//     ? Math.exp(50 * Math.log(Q[index]) * (1 / BUI - 1 / BUIo[index]))
//     : 1
// }

function createRaster() {
  const raster = new olSource.Raster({
    sources: [easSource, ftlSource],

    operation: (layers: any, data: any): number[] | ImageData => {
      const ISIcalc = (ffmc: number, ws: number, fbpMod: boolean = false): number => {
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
          ws >= 40 && fbpMod
            ? 12 * (1 - Math.exp(-0.0818 * (ws - 28)))
            : Math.exp(0.05039 * ws)
        // #Eq. 25 - Fine Fuel Moisture
        // fF <- 91.9 * exp(-0.1386 * fm) * (1 + (fm^5.31) / 49300000)
        const fF = 91.9 * Math.exp(-0.1386 * fm) * (1 + Math.pow(fm, 5.31) / 49300000)
        // #Eq. 26 - Spread Index Equation
        // isi <- 0.208 * fW * fF
        return 0.208 * fW * fF
        // return(isi)
      }

      const calcROSColour = (ros: number, opacity: number): number[] => {
        if (ros < 0) {
          if (ros === -2) {
            // it's water - or something that doesn't burn.
            return [0, 0, 0, 0]
          }
          // don't know what this is!
          return [0x0, 0x0, 0x0, opacity]
        }
        // return [0xff, 0x00, 0x00, 0xff]
        if (ros < 3) {
          // low, green
          return [0, 128, 0, opacity]
        } else if (ros < 8) {
          // moderate, yellow
          return [255, 255, 0x0, opacity]
        } else if (ros < 15) {
          // high, orange
          return [255, 165, 0, opacity]
        }
        // extreme, red
        return [255, 0, 0, opacity]

        // gradient:
        // return [0xff, Math.max(0, 255 - (ros / 100) * 255), 0x00, opacity]
        // matching redbook:
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

      const ftlNumberToFtlCode = (ftlNumber: number): string | undefined => {
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
          case 6:
            // Not sure - but seems logical?
            return 'C6'
          case 7:
            return 'C7'
          case 11:
            return 'D1'
          case 12:
            return 'D1'
          case 13:
            return 'D1'
        }
        if (ftlNumber >= 500 && ftlNumber < 700) {
          return 'M1'
        }
        return undefined
      }

      const ROScalc = (
        FUELTYPE: string,
        ISI: number,
        BUI: number,
        FMC: number,
        SFC: number | undefined = undefined,
        PC: number | undefined = undefined,
        PDF: number | undefined = undefined,
        CC: number | undefined = undefined,
        CBH: number
      ): number => {
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
        const a = [
          90,
          110,
          110,
          110,
          30,
          30,
          45,
          30,
          0,
          0,
          120,
          100,
          75,
          40,
          55,
          190,
          250
        ]
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
        if (
          ['C1', 'C2', 'C3', 'C4', 'C5', 'C7', 'D1', 'S1', 'S2', 'S3'].includes(FUELTYPE)
        ) {
          rsi = a[index] * Math.pow(1 - Math.exp(-b[index] * ISI), c0[index])
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
            throw new Error('PC not specified')
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
            throw new Error('PC not specified')
          }
          rsi =
            (PC / 100) * ROScalc('C2', ISI, NoBUI, FMC, SFC, PC, PDF, CC, CBH) +
            ((0.2 * (100 - PC)) / 100) *
              ROScalc('D1', ISI, NoBUI, FMC, SFC, PC, PDF, CC, CBH)
        }

        // #Initial Rate of Spread for M3 Mixedwood
        // RSI_m3 <- rep(-99,length(ISI))
        // #Eq. 30 (Wotton et. al 2009)
        // RSI_m3 <-
        //   ifelse(FUELTYPE %in% c("M3"),
        //     as.numeric(a[["M3"]] * ((1 - exp(-b[["M3"]] * ISI))**c0[["M3"]])), RSI_m3)
        // #Eq. 29 (Wotton et. al 2009)
        // RSI <-
        //   ifelse(FUELTYPE %in% c("M3"),
        //     PDF/100* RSI_m3 + (1-PDF/100) *
        //       .ROScalc(rep("D1", length(ISI)), ISI, NoBUI, FMC, SFC, PC, PDF, CC,CBH),
        //     RSI)
        else if (FUELTYPE === 'M3') {
          if (!PDF) {
            throw new Error('PDF not specified')
          }
          const RSI_m3 = a[index] * Math.pow(1 - Math.exp(-b[index] * ISI), c0[index])
          rsi =
            (PDF / 100) * RSI_m3 +
            (1 - PDF / 100) * ROScalc('D1', ISI, NoBUI, FMC, SFC, PC, PDF, CC, CBH)
        }
        // #Initial Rate of Spread for M4 Mixedwood
        // RSI_m4 <- rep(-99,length(ISI))
        // #Eq. 30 (Wotton et. al 2009)
        // RSI_m4 <-
        //   ifelse(FUELTYPE %in% c("M4"),
        //     as.numeric(a[["M4"]] * ((1 - exp(-b[["M4"]] * ISI))**c0[["M4"]])), RSI_m4)
        // #Eq. 33 (Wotton et. al 2009)
        // RSI <-
        //   ifelse(FUELTYPE %in% c("M4"),
        //     PDF / 100* RSI_m4 + 0.2 * (1 - PDF / 100)*
        //       .ROScalc(rep("D1", length(ISI)), ISI, NoBUI, FMC, SFC, PC, PDF, CC,CBH),
        //     RSI)
        else if (FUELTYPE === 'M4') {
          if (!PDF) {
            throw new Error('PDF not specified')
          }
          const RSI_m4 = a[index] * Math.pow(1 - Math.exp(-b[index] * ISI), c0[index])
          rsi =
            (PDF / 100) * RSI_m4 +
            0.2 * (1 - PDF / 100) * ROScalc('D1', ISI, NoBUI, FMC, SFC, PC, PDF, CC, CBH)
        }
        // #Eq. 35b (Wotton et. al. 2009) - Calculate Curing function for grass
        // CF <- rep(-99,length(ISI))
        // CF <-
        //   ifelse(FUELTYPE %in% c("O1A", "O1B"),
        //          ifelse(CC < 58.8,
        //                 0.005 * (exp(0.061 * CC) - 1),
        //                 0.176 + 0.02 * (CC - 58.8)),
        //          CF)
        // #Eq. 36 (FCFDG 1992) - Calculate Initial Rate of Spread for Grass
        // RSI <-
        //   ifelse(FUELTYPE %in% c("O1A", "O1B"),
        //     a[FUELTYPE] * ((1 - exp(-b[FUELTYPE] * ISI))**c0[FUELTYPE]) * CF,
        //   RSI)
        else if (FUELTYPE === 'O1A' || FUELTYPE === 'O1B') {
          if (!CC) {
            throw Error('CC not specified')
          }
          const CF =
            CC < 58.8 ? 0.005 * (Math.exp(0.061 * CC) - 1) : 0.176 + 0.02 * (CC - 58.8)
          rsi = a[index] * Math.pow(1 - Math.exp(-b[index] * ISI), c0[index]) * CF
        }
        // #Calculate C6 separately
        // ROS <-
        //   ifelse(FUELTYPE %in% c("C6"),
        //     .C6calc(FUELTYPE, ISI, BUI, FMC, SFC, CBH, option = "ROS"),
        //     .BEcalc(FUELTYPE, BUI) * RSI)
        // #add a constraint
        // ROS <- ifelse(ROS <= 0,0.000001,ROS)
        let ros: number
        if (FUELTYPE === 'C6') {
          ros = C6calc(
            FUELTYPE,
            ISI,
            BUI,
            FMC,
            SFC,
            CBH,
            undefined,
            undefined,
            undefined,
            'ROS'
          )
        } else {
          ros = BEcalc(FUELTYPE, BUI) * rsi
        }

        return ros <= 0 ? 0.000001 : ros
      }

      const BEcalc = (FUELTYPE: string, BUI: number): number => {
        // #############################################################################
        // # Description:
        // #   Computes the Buildup Effect on Fire Spread Rate.
        // #
        // #   All variables names are laid out in the same manner as Forestry Canada
        // #   Fire Danger Group (FCFDG) (1992). Development and Structure of the
        // #   Canadian Forest Fire Behavior Prediction System." Technical Report
        // #   ST-X-3, Forestry Canada, Ottawa, Ontario.
        // #
        // # Args:
        // #   FUELTYPE: The Fire Behaviour Prediction FuelType
        // #   BUI:      The Buildup Index value
        // # Returns:
        // #   BE: The Buildup Effect
        // #
        // #############################################################################
        // #Fuel Type String represenations
        // d <- c("C1", "C2", "C3", "C4", "C5", "C6", "C7", "D1", "M1", "M2", "M3",
        //        "M4","S1", "S2", "S3", "O1A", "O1B")
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
        // #The average BUI for the fuel type - as referenced by the "d" list above
        // BUIo <- c(72, 64, 62, 66, 56, 62, 106, 32, 50, 50, 50, 50, 38, 63, 31, 01,
        //           01)
        const BUIo = [72, 64, 62, 66, 56, 62, 106, 32, 50, 50, 50, 50, 38, 63, 31, 1, 1]
        // #Proportion of maximum possible spread rate that is reached at a standard BUI
        // Q <- c(0.9, 0.7, 0.75, 0.8, 0.8, 0.8, 0.85, 0.9, 0.8, 0.8, 0.8, 0.8, 0.75,
        //        0.75, 0.75, 1.0, 1.0)
        const Q = [
          0.9,
          0.7,
          0.75,
          0.8,
          0.8,
          0.8,
          0.85,
          0.9,
          0.8,
          0.8,
          0.8,
          0.8,
          0.75,
          0.75,
          0.75,
          1.0,
          1.0
        ]
        // names(BUIo) <- names(Q)<-d
        const index = d.indexOf(FUELTYPE)

        // #Eq. 54 (FCFDG 1992) The Buildup Effect
        // BE<- ifelse(BUI > 0 & BUIo[FUELTYPE] > 0,
        //   exp(50 * log(Q[FUELTYPE]) * (1 / BUI - 1 / BUIo[FUELTYPE])), 1)
        // return(as.numeric(BE))
        return BUI > 0 && BUIo[index] > 0
          ? Math.exp(50 * Math.log(Q[index]) * (1 / BUI - 1 / BUIo[index]))
          : 1
      }

      const C6calc = (
        FUELTYPE: string,
        ISI: number,
        BUI: number,
        FMC: number,
        SFC: number | undefined,
        CBH: number | undefined,
        ROS: number | undefined,
        CFB: number | undefined,
        RSC: number | undefined,
        option: string = 'CFB'
      ): number => {
        //     .C6calc<-function(FUELTYPE, ISI, BUI, FMC, SFC, CBH, ROS, CFB, RSC,
        //       option="CFB"){
        // #############################################################################
        // # Description:
        // #   Calculate c6 (Conifer plantation) Fire Spread. C6 is a special case, and
        // #     thus has it's own function. To calculate C6 fire spread, this function
        // #     also calculates and can return ROS, CFB, RSC, or RSI by specifying in
        // #     the option parameter.
        // #
        // #   All variables names are laid out in the same manner as Forestry Canada
        // #   Fire Danger Group (FCFDG) (1992). Development and Structure of the
        // #   Canadian Forest Fire Behavior Prediction System." Technical Report
        // #   ST-X-3, Forestry Canada, Ottawa, Ontario.
        // #
        // # Args:
        // #   FUELTYPE: The Fire Behaviour Prediction FuelType
        // #   ISI:      Initial Spread Index
        // #   BUI:      Buildup Index
        // #   FMC:      Foliar Moisture Content
        // #   SFC:      Surface Fuel Consumption
        // #   CBH:      Crown Base Height
        // #   ROS:      Rate of Spread
        // #   CFB:      Crown Fraction Burned
        // #   RSC:      Crown Fire Spread Rate (m/min)
        // #   option:   Which variable to calculate(ROS, CFB, RSC, or RSI)
        // #
        // # Returns:
        // #   ROS, CFB, RSC or RSI depending on which option was selected
        // #
        // #############################################################################
        // #Average foliar moisture effect
        // FMEavg <- 0.778
        const FMEavg = 0.778
        // #Eq. 59 (FCFDG 1992) Crown flame temperature (degrees K)
        // tt <- 1500 - 2.75 * FMC
        // const tt = 1500 - 2.75 * FMC
        // #Eq. 60 (FCFDG 1992) Head of ignition (kJ/kg)
        // H <- 460 + 25.9 * FMC
        // const H = 460 + 25.9 * FMC
        // #Eq. 61 (FCFDG 1992) Average foliar moisture effect
        // FME <- ((1.5 - 0.00275 * FMC)**4.)/(460 + 25.9 * FMC) * 1000
        const FME = (Math.pow(1.5 - 0.00275 * FMC, 4.0) / (460 + 25.9 * FMC)) * 1000
        // #Eq. 62 (FCFDG 1992) Intermediate surface fire spread rate
        // RSI <- 30 * (1 - exp(-0.08 * ISI))**3.0
        const RSI = 30 * Math.pow(1 - Math.exp(-0.08 * ISI), 3.0)
        // #Return at this point, if specified by caller
        // if(option=="RSI"){
        // return(RSI)
        // }
        if (option === 'RSI') {
          return RSI
        }
        // #Eq. 63 (FCFDG 1992) Surface fire spread rate (m/min)
        // RSS <- RSI * .BEcalc(FUELTYPE, BUI)
        const RSS = RSI * BEcalc(FUELTYPE, BUI)
        // #Eq. 64 (FCFDG 1992) Crown fire spread rate (m/min)
        // RSC <- 60 * (1 - exp(-0.0497 * ISI)) * FME / FMEavg
        RSC = (60 * (1 - Math.exp(-0.0497 * ISI)) * FME) / FMEavg
        // #Return at this point, if specified by caller
        // if(option=="RSC"){
        // return(RSC)
        // }
        if (option === 'RSC') {
          return RSC
        }
        // #Crown Fraction Burned
        // CFB    <- ifelse(RSC > RSS,.CFBcalc(FUELTYPE, FMC, SFC, RSS, CBH),0)
        if (!SFC) {
          throw new Error('SFC not specified')
        }
        if (!CBH) {
          throw new Error('CBH not specified')
        }
        CFB = RSC > RSS ? CFBcalc(FUELTYPE, FMC, SFC, RSS, CBH) : 0
        // #Return at this point, if specified by caller
        // if(option=="CFB"){
        // return(CFB)
        // }
        if (option === 'CFB') {
          return CFB
        }
        // #Eq. 65 (FCFDG 1992) Calculate Rate of spread (m/min)
        // ROS    <- ifelse(RSC > RSS,RSS + (CFB)*(RSC-RSS),RSS)
        // return(ROS)
        // }
        return RSC > RSS ? RSS + CFB * (RSC - RSS) : RSS
      }

      const CFBcalc = (
        FUELTYPE: string,
        FMC: number,
        SFC: number,
        ROS: number,
        CBH: number,
        option = 'CFB'
      ): number => {
        // .CFBcalc <- function(FUELTYPE, FMC, SFC, ROS, CBH, option="CFB"){
        //   #############################################################################
        //   # Description:
        //   #   Calculate Calculate Crown Fraction Burned. To calculate CFB, we also
        //   #     need to calculate Critical surface intensity (CSI), and Surface fire
        //   #     rate of spread (RSO). The value of each of these equations can be
        //   #     returned to the calling function without unecessary additional
        //   #     calculations.
        //   #
        //   #   All variables names are laid out in the same manner as Forestry Canada
        //   #   Fire Danger Group (FCFDG) (1992). Development and Structure of the
        //   #   Canadian Forest Fire Behavior Prediction System." Technical Report
        //   #   ST-X-3, Forestry Canada, Ottawa, Ontario.
        //   #
        //   # Args:
        //   #   FUELTYPE: The Fire Behaviour Prediction FuelType
        //   #   FMC:      Foliar Moisture Content
        //   #   SFC:      Surface Fuel Consumption
        //   #   CBH:      Crown Base Height
        //   #   ROS:      Rate of Spread
        //   #   option:   Which variable to calculate(ROS, CFB, RSC, or RSI)

        //   # Returns:
        //   #   CFB, CSI, RSO depending on which option was selected.
        //   #
        //   #############################################################################
        //   CFB <- 0
        let CFB = 0
        //   #Eq. 56 (FCFDG 1992) Critical surface intensity
        //   CSI <- 0.001 * (CBH**1.5) * (460 + 25.9 * FMC)**1.5
        const CSI = 0.001 * Math.pow(CBH, 1.5) * Math.pow(460 + 25.9 * FMC, 1.5)
        //   #Return at this point, if specified by caller
        //   if(option=="CSI"){
        //     return(CSI)
        //   }
        if (option === 'CSI') {
          return CSI
        }
        //   #Eq. 57 (FCFDG 1992) Surface fire rate of spread (m/min)
        //   RSO <- CSI / (300 * SFC)
        const RSO = CSI / (300 * SFC)
        //   #Return at this point, if specified by caller
        //   if(option=="RSO"){
        //     return(RSO)
        //   }
        if (option === 'RSO') {
          return RSO
        }
        //   #Eq. 58 (FCFDG 1992) Crown fraction burned
        //   CFB <- ifelse(ROS > RSO, 1 - exp(-0.23 * (ROS - RSO)), CFB)
        CFB = ROS > RSO ? 1 - Math.exp(-0.23 * (ROS - RSO)) : CFB
        //   return(CFB)
        // }
        return CFB
      }

      const SFCCalc = (
        FUELTYPE: string,
        FFMC: number,
        BUI: number,
        PC: number,
        GFL: number | undefined
      ): number => {
        // .SFCcalc <- function(FUELTYPE, FFMC, BUI, PC, GFL) {
        //   #############################################################################
        //   # Description:
        //   #   Computes the Surface Fuel Consumption by Fuel Type.
        //   #   All variables names are laid out in the same manner as FCFDG (1992) or
        //   #   Wotton et. al (2009)
        //   #   Forestry Canada Fire Danger Group (FCFDG) (1992). "Development and
        //   #   Structure of the Canadian Forest Fire Behavior Prediction System."
        //   #   Technical Report ST-X-3, Forestry Canada, Ottawa, Ontario.
        //   #
        //   #   Wotton, B.M., Alexander, M.E., Taylor, S.W. 2009. Updates and revisions to
        //   #   the 1992 Canadian forest fire behavior prediction system. Nat. Resour.
        //   #   Can., Can. For. Serv., Great Lakes For. Cent., Sault Ste. Marie, Ontario,
        //   #   Canada. Information Report GLC-X-10, 45p.
        //   #
        //   # Args:
        //   #   FUELTYPE: The Fire Behaviour Prediction FuelType
        //   #        BUI: Buildup Index
        //   #       FFMC: Fine Fuel Moisture Code
        //   #         PC: Percent Conifer (%)
        //   #        GFL: Grass Fuel Load (kg/m^2)
        //   # Returns:
        //   #        SFC: Surface Fuel Consumption (kg/m^2)
        //   #
        //   #############################################################################
        //   SFC <- rep(-999,length(FFMC))
        let SFC = -999
        //   #Eqs. 9a, 9b (Wotton et. al. 2009) - Solving the lower bound of FFMC value
        //   # for the C1 fuel type SFC calculation
        //   SFC <- ifelse(FUELTYPE=="C1",
        //           ifelse(FFMC > 84,
        //             0.75 + 0.75 * (1 - exp(-0.23 * (FFMC - 84)))**0.5,
        //             0.75 - 0.75 * (1 - exp(-0.23 * (84 - FFMC)))**0.5),
        //           SFC)
        if (FUELTYPE === 'C1') {
          SFC =
            FFMC > 84
              ? 0.75 + 0.75 * Math.pow(1 - Math.exp(-0.23 * (FFMC - 84)), 0.5)
              : 0.75 - 0.75 * Math.pow(1 - Math.exp(-0.23 * (84 - FFMC)), 0.5)
        }
        //   #Eq. 10 (FCFDG 1992) - C2, M3, and M4 Fuel Types
        //   SFC <- ifelse(FUELTYPE == "C2" | FUELTYPE == "M3" | FUELTYPE == "M4",
        //           5.0 * (1 - exp(-0.0115 * BUI)),
        //           SFC)
        else if (FUELTYPE === 'C2' || FUELTYPE === 'M3' || FUELTYPE === 'M4') {
          SFC = 5.0 * (1 - Math.exp(-0.0115 * BUI))
        }
        //   #Eq. 11 (FCFDG 1992) - C3, C4 Fuel Types
        //   SFC <- ifelse(FUELTYPE == "C3" | FUELTYPE == "C4",
        //           5.0 * (1 - exp(-0.0164 * BUI))**2.24,
        //           SFC)
        else if (FUELTYPE === 'C3' || FUELTYPE === 'C4') {
          SFC = 5.0 * (1 - Math.exp(-0.0164 * BUI)) ** 2.24
        }
        //   #Eq. 12 (FCFDG 1992) - C5, C6 Fuel Types
        //   SFC <- ifelse(FUELTYPE == "C5" | FUELTYPE == "C6",
        //           5.0 * (1 - exp(-0.0149 * BUI))**2.48,
        //           SFC)
        else if (FUELTYPE === 'C5' || FUELTYPE === 'C6') {
          SFC = 5.0 * (1 - Math.exp(-0.0149 * BUI)) ** 2.48
        }
        //   #Eqs. 13, 14, 15 (FCFDG 1992) - C7 Fuel Types
        // SFC <- ifelse(FUELTYPE == "C7",
        //         ifelse(FFMC > 70, 2 * (1 - exp(-0.104 * (FFMC - 70))),
        //           0) + 1.5 * (1 - exp(-0.0201 * BUI)),
        //         SFC)
        else if (FUELTYPE === 'C7') {
          const tmp = FFMC > 70 ? 2 * (1 - Math.exp(-0.104 * (FFMC - 70))) : 0
          SFC = tmp + 1.5 * (1 - Math.exp(-0.0201 * BUI))
        }
        //   #Eq. 16 (FCFDG 1992) - D1 Fuel Type
        //   SFC <- ifelse(FUELTYPE == "D1", 1.5 * (1 - exp(-0.0183 * BUI)), SFC)
        else if (FUELTYPE === 'D1') {
          SFC = 1.5 * (1 - Math.exp(-0.0183 * BUI))
        }
        //   #Eq. 17 (FCFDG 1992) - M1 and M2 Fuel Types
        //   SFC <- ifelse(FUELTYPE == "M1" | FUELTYPE == "M2",
        //           PC / 100 * (5.0 * (1 - exp(-0.0115 * BUI))) +
        //            ((100 - PC) / 100 * (1.5 * (1 - exp(-0.0183 * BUI)))),
        //           SFC)
        else if (FUELTYPE === 'M1' || FUELTYPE === 'M2') {
          SFC =
            (PC / 100) * (5.0 * (1 - Math.exp(-0.0115 * BUI))) +
            ((100 - PC) / 100) * (1.5 * (1 - Math.exp(-0.0183 * BUI)))
        }
        //   #Eq. 18 (FCFDG 1992) - Grass Fuel Types
        //   SFC <- ifelse(FUELTYPE == "O1A" | FUELTYPE == "O1B", GFL, SFC)
        else if (FUELTYPE === 'O1A' || FUELTYPE === 'O1B') {
          if (!GFL) {
            throw new Error('GFL not provided')
          }
          SFC = GFL
        }
        //   #Eq. 19, 20, 25 (FCFDG 1992) - S1 Fuel Type
        //   SFC <- ifelse(FUELTYPE == "S1",
        //           4.0 * (1 - exp(-0.025 * BUI)) + 4.0 * (1 - exp(-0.034 * BUI)),
        //           SFC)
        else if (FUELTYPE === 'S1') {
          SFC = 4.0 * (1 - Math.exp(-0.025 * BUI)) + 4.0 * (1 - Math.exp(-0.034 * BUI))
        }
        //   #Eq. 21, 22, 25 (FCFDG 1992) - S2 Fuel Type
        //   SFC <- ifelse(FUELTYPE == "S2",
        //           10.0 * (1 - exp(-0.013 * BUI)) + 6.0 * (1 - exp(-0.060 * BUI)),
        //           SFC)
        else if (FUELTYPE === 'S2') {
          SFC = 10.0 * (1 - Math.exp(-0.013 * BUI)) + 6.0 * (1 - Math.exp(-0.06 * BUI))
        }
        //   #Eq. 23, 24, 25 (FCFDG 1992) - S3 Fuel Type
        //   SFC <- ifelse(FUELTYPE == "S3",
        //           12.0 * (1 - exp(-0.0166 * BUI)) + 20.0 * (1-exp(-0.0210 * BUI)),
        //           SFC)
        else if (FUELTYPE === 'S3') {
          SFC = 12.0 * (1 - Math.exp(-0.0166 * BUI)) + 20.0 * (1 - Math.exp(-0.021 * BUI))
        }
        //   #Constrain SFC value
        //   SFC <- ifelse(SFC <= 0, 0.000001, SFC)
        //   return(SFC)
        // }
        return SFC <= 0 ? 0.000001 : SFC
      }

      const isNonFuel = (ftlNumber: number): boolean => {
        switch (ftlNumber) {
          case 101:
          case 102:
          case 103:
            return true
        }
        return false
        // if (ftlNumber >= 99 && ftlNumber < 200) {
        //   // case 101: // NonFuel
        //   // case 102: // Water
        //   // case 106: // Urban
        //   // the rest - no idea!
        //   return true
        // }
        // return false
      }

      const Slopecalc = (
        FUELTYPE: string,
        FFMC: number,
        BUI: number,
        WS: number,
        WAZ: number,
        GS: number,
        SAZ: number,
        FMC: number,
        SFC: number | undefined,
        PC: number,
        PDF: number | undefined,
        CC: number | undefined,
        CBH: number,
        ISI: number | undefined,
        output: string = 'RAZ'
      ): number => {
        // .Slopecalc <- function(FUELTYPE, FFMC, BUI, WS, WAZ, GS, SAZ, FMC, SFC, PC, PDF,
        //   CC, CBH, ISI, output = "RAZ") {
        //   # output options include: RAZ and WSV
        //   #############################################################################
        //   # Description:
        //   #   Calculate the net effective windspeed (WSV), the net effective wind
        //   #   direction (RAZ) or the wind azimuth (WAZ).
        //   #
        //   #   All variables names are laid out in the same manner as FCFDG (1992) and
        //   #   Wotton (2009).
        //   #
        //   #
        //   #   Forestry Canada Fire Danger Group (FCFDG) (1992). "Development and
        //   #   Structure of the Canadian Forest Fire Behavior Prediction System."
        //   #   Technical Report ST-X-3, Forestry Canada, Ottawa, Ontario.
        //   #
        //   #   Wotton, B.M., Alexander, M.E., Taylor, S.W. 2009. Updates and revisions to
        //   #   the 1992 Canadian forest fire behavior prediction system. Nat. Resour.
        //   #   Can., Can. For. Serv., Great Lakes For. Cent., Sault Ste. Marie, Ontario,
        //   #   Canada. Information Report GLC-X-10, 45p.
        //   #
        //   # Args:
        //   #   FUELTYPE: The Fire Behaviour Prediction FuelType
        //   #       FFMC: Fine Fuel Moisture Code
        //   #        BUI: The Buildup Index value
        //   #         WS: Windspeed (km/h)
        //   #        WAZ: Wind Azimuth
        //   #         GS: Ground Slope (%)
        //   #        SAZ: Slope Azimuth
        //   #        FMC: Foliar Moisture Content
        //   #        SFC: Surface Fuel Consumption (kg/m^2)
        //   #         PC: Percent Conifer (%)
        //   #        PDF: Percent Dead Balsam Fir (%)
        //   #         CC: Constant
        //   #        CBH: Crown Base Height (m)
        //   #        ISI: Initial Spread Index
        //   #     output: Type of variable to output (RAZ/WSV, default=RAZ)
        //   # Returns:
        //   #   BE: The Buildup Effect
        //   #
        //   #############################################################################
        //   #check for valid output types
        //   validOutTypes = c("RAZ", "WAZ", "WSV")
        //   if(!(output %in% validOutTypes)){
        //   stop(paste("In 'slopecalc()', '",output, "' is an invalid 'output' type.",
        //   sep=""))
        //   }
        if (!['RAZ', 'WAZ', 'WSV'].includes(output)) {
          throw Error("In 'slopecalc()', '" + output + "' is an invalid 'output' type.")
        }
        //   NoBUI <- rep(-1,length(FFMC))
        const NoBUI = -1
        //   #Eq. 39 (FCFDG 1992) - Calculate Spread Factor
        //   SF <- ifelse (GS >= 70, 10, exp(3.533 * (GS / 100)^1.2))
        const SF = GS >= 70 ? 10 : Math.exp(3.533 * Math.pow(GS / 100, 1.2))
        //   #ISI with 0 wind on level grounds
        //   ISZ <- .ISIcalc(FFMC, 0)
        const ISZ = ISIcalc(FFMC, 0)
        //   #Surface spread rate with 0 wind on level ground
        //   RSZ <- .ROScalc(FUELTYPE, ISZ, BUI = NoBUI, FMC, SFC, PC, PDF, CC, CBH)
        let RSZ = ROScalc(FUELTYPE, ISZ, NoBUI, FMC, SFC, PC, PDF, CC, CBH)
        //   #Eq. 40 (FCFDG 1992) - Surface spread rate with 0 wind upslope
        //   RSF <- RSZ * SF
        const RSF = RSZ * SF
        //   #setup some reference vectors
        //   d <- c("C1", "C2", "C3", "C4", "C5", "C6", "C7", "D1", "M1", "M2", "M3", "M4",
        //   "S1", "S2", "S3", "O1A", "O1B")
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
        const index = d.indexOf(FUELTYPE)
        const c2_index = d.indexOf('C2')
        const d1_index = d.indexOf('D1')
        //   a <- c(90, 110, 110, 110, 30, 30, 45, 30, 0, 0, 120, 100, 75, 40, 55, 190,
        //   250)
        const a = [
          90,
          110,
          110,
          110,
          30,
          30,
          45,
          30,
          0,
          0,
          120,
          100,
          75,
          40,
          55,
          190,
          250
        ]
        //   b <- c(0.0649, 0.0282, 0.0444, 0.0293, 0.0697, 0.0800, 0.0305, 0.0232, 0, 0,
        //   0.0572, 0.0404, 0.0297, 0.0438, 0.0829, 0.0310, 0.0350)
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
        //   c0 <- c(4.5, 1.5, 3.0, 1.5, 4.0, 3.0, 2.0, 1.6, 0, 0, 1.4, 1.48, 1.3, 1.7,
        //   3.2, 1.4, 1.7)
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
        //   names(a) <- names(b) <- names(c0) <- d

        //   #initialize some local vars
        //   RSZ <- rep(-99,length(FFMC))
        RSZ = -99
        //   RSF_C2 <- rep(-99,length(FFMC))
        //   RSF_D1 <- rep(-99,length(FFMC))
        //   RSF_M3 <- rep(-99,length(FFMC))
        //   RSF_M4 <- rep(-99,length(FFMC))
        //   CF <- rep(-99,length(FFMC))
        //   ISF <- rep(-99,length(FFMC))
        let ISF = -99
        //   ISF_C2 <- rep(-99,length(FFMC))
        //   ISF_D1 <- rep(-99,length(FFMC))
        //   ISF_M3 <- rep(-99,length(FFMC))
        //   ISF_M4 <- rep(-99,length(FFMC))

        //   #Eqs. 41a, 41b (Wotton 2009) - Calculate the slope equivalend ISI
        //   ISF <- ifelse(FUELTYPE %in% c("C1", "C2", "C3", "C4", "C5", "C6", "C7", "D1",
        //               "S1", "S2", "S3"),
        //   ifelse((1 - (RSF / a[FUELTYPE])**(1 / c0[FUELTYPE])) >= 0.01,
        //   log(1 - (RSF / a[FUELTYPE])**(1 / c0[FUELTYPE])) / (-b[FUELTYPE]),
        //   log(0.01)/(-b[FUELTYPE])),
        //   ISF)
        if (
          ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'D1', 'S1', 'S2', 'S3'].includes(
            FUELTYPE
          )
        ) {
          ISF =
            1 - Math.pow(RSF / a[index], 1 / c0[index]) >= 0.01
              ? Math.log(1 - Math.pow(RSF / a[index], 1 / c0[index])) / -b[index]
              : Math.log(0.01) / -b[index]
        }
        //   #When calculating the M1/M2 types, we are going to calculate for both C2
        //   # and D1 types, and combine
        //   #Surface spread rate with 0 wind on level ground
        else if (['M1', 'M2'].includes(FUELTYPE)) {
          // RSZ <- ifelse(FUELTYPE %in% c("M1", "M2"),
          //        .ROScalc(rep("C2", length(ISZ)), ISZ, BUI = NoBUI, FMC, SFC, PC, PDF,
          //                 CC, CBH),
          //        RSZ)
          let RSZ = ROScalc('C2', ISZ, NoBUI, FMC, SFC, PC, PDF, CC, CBH)
          // #Eq. 40 (FCFDG 1992) - Surface spread rate with 0 wind upslope for C2
          // RSF_C2 <- ifelse(FUELTYPE %in% c("M1", "M2"), RSZ * SF, RSF_C2)
          const RSF_C2 = RSZ * SF
          // RSZ <- ifelse(FUELTYPE %in% c("M1", "M2"),
          //         .ROScalc(rep("D1", length(ISZ)), ISZ, BUI = NoBUI, FMC, SFC, PC,
          //                   PDF, CC, CBH),RSZ)
          RSZ = ROScalc('D1', ISZ, NoBUI, FMC, SFC, PC, PDF, CC, CBH)
          // #Eq. 40 (FCFDG 1992) - Surface spread rate with 0 wind upslope for D1
          // RSF_D1 <- ifelse(FUELTYPE %in% c("M1", "M2"), RSZ * SF, RSF_D1)
          // RSF0 <- 1 - (RSF_C2 / a[["C2"]])^(1 / c0[["C2"]])
          const RSF_D1 = RSZ * SF
          let RSF0 = 1 - Math.pow(RSF_C2 / a[c2_index], 1 / c0[c2_index])
          // #Eq. 41a (Wotton 2009) - Calculate the slope equivalent ISI
          // ISF_C2 <- ifelse(FUELTYPE %in% c("M1", "M2") & RSF0 >= 0.01,
          //             log(1 - (RSF_C2 / a[["C2"]])**(1 / c0[["C2"]])) / (-b[["C2"]]),
          //             ISF_C2)
          // #Eq. 41b (Wotton 2009) - Calculate the slope equivalent ISI
          // ISF_C2 <- ifelse(FUELTYPE %in% c("M1", "M2") & RSF0 < 0.01,
          //             log(0.01) / (-b[["C2"]]),
          //             ISF_C2)
          const ISF_C2 =
            RSF0 >= 0.01
              ? Math.log(1 - Math.pow(RSF_C2 / a[c2_index], 1 / c0[c2_index])) /
                -b[c2_index]
              : Math.log(0.01) / -b[c2_index]
          // RSF0 <- 1 - (RSF_D1 / a[["D1"]])^(1 / c0[["D1"]])
          RSF0 = (1 - RSF_D1 / a[d1_index]) ^ (1 / c0[d1_index])
          // #Eq. 41a (Wotton 2009) - Calculate the slope equivalent ISI
          // ISF_D1 <- ifelse(FUELTYPE %in% c("M1", "M2") & RSF0 >= 0.01,
          //             log(1 - (RSF_D1 / a[["D1"]])**(1 / c0[["D1"]])) / (-b[["D1"]]),
          //             ISF_D1)
          // #Eq. 41b (Wotton 2009) - Calculate the slope equivalent ISI
          // ISF_D1 <- ifelse(FUELTYPE %in% c("M1", "M2") & RSF0 < 0.01,
          //             log(0.01) / (-b[["D1"]]),
          //             ISF_D1)
          const ISF_D1 =
            RSF0 >= 0.01
              ? Math.log(1 - Math.pow(RSF_D1 / a[d1_index], 1 / c0[d1_index])) /
                -b[d1_index]
              : Math.log(0.01) / -b[d1_index]
          // #Eq. 42a (Wotton 2009) - Calculate weighted average for the M1/M2 types
          // ISF <- ifelse(FUELTYPE %in% c("M1", "M2"), PC / 100 * ISF_C2 +
          //                 (1 - PC / 100) * ISF_D1,
          //               ISF)
          ISF = (PC / 100) * ISF_C2 + (1 - PC / 100) * ISF_D1
        } else if (FUELTYPE === 'M3') {
          //   #Set % Dead Balsam Fir to 100%
          //   PDF100 <- rep(100, length(ISI))
          //   #Surface spread rate with 0 wind on level ground
          //   RSZ <- ifelse(FUELTYPE %in% c("M3"),
          //   .ROScalc(rep("M3", length(FMC)), ISI = ISZ, BUI = NoBUI, FMC, SFC,
          //   PC, PDF100, CC, CBH),
          //   RSZ)
          //   #Eq. 40 (FCFDG 1992) - Surface spread rate with 0 wind upslope for M3
          //   RSF_M3 <- ifelse(FUELTYPE %in% c("M3"), RSZ * SF, RSF_M3)
          //   #Surface spread rate with 0 wind on level ground, using D1
          //   RSZ <- ifelse(FUELTYPE %in% c("M3"),
          //   .ROScalc(rep("D1", length(ISZ)), ISZ, BUI = NoBUI, FMC, SFC, PC,
          //   PDF100, CC, CBH),
          //   RSZ)
          //   #Eq. 40 (FCFDG 1992) - Surface spread rate with 0 wind upslope for M3
          //   RSF_D1 <- ifelse(FUELTYPE %in% c("M3"), RSZ * SF, RSF_D1)
          //   RSF0 <- 1 - (RSF_M3 / a[["M3"]])^(1 / c0[["M3"]])
          //   #Eq. 41a (Wotton 2009) - Calculate the slope equivalent ISI
          //   ISF_M3 <- ifelse(FUELTYPE %in% c("M3") & RSF0 >= 0.01,
          //   log(1 - (RSF_M3/a[["M3"]])**(1/c0[["M3"]]))/(-b[["M3"]]),ISF_M3)
          //   #Eq. 41b (Wotton 2009) - Calculate the slope equivalent ISI
          //   ISF_M3 <- ifelse(FUELTYPE %in% c("M3") & RSF0 < 0.01,
          //   log(0.01) / (-b[["M3"]]),
          //   ISF_M3)
          //   #Eq. 40 (FCFDG 1992) - Surface spread rate with 0 wind upslope for D1
          //   RSF0 <- 1 - (RSF_D1 / a[["D1"]])^(1 / c0[["D1"]])
          //   #Eq. 41a (Wotton 2009) - Calculate the slope equivalent ISI
          //   ISF_D1 <- ifelse(FUELTYPE %in% c("M3") & RSF0 >= 0.01,
          //   log(1 - (RSF_D1 / a[["D1"]])**(1 / c0[["D1"]])) / (-b[["D1"]]),
          //   ISF_D1)
          //   #Eq. 41b (Wotton 2009) - Calculate the slope equivalent ISI
          //   ISF_D1 <- ifelse(FUELTYPE %in% c("M3") & RSF0 < 0.01,
          //   log(0.01) / (-b[["D1"]]),
          //   ISF_D1)
          //   #Eq. 42b (Wotton 2009) - Calculate weighted average for the M3 type
          //   ISF <- ifelse(FUELTYPE %in% c("M3"),
          //   PDF / 100 * ISF_M3 + (1 - PDF / 100) * ISF_D1,
          //   ISF)
          throw Error('slope for M3 not implemented')
        }
        //   #Surface spread rate with 0 wind on level ground, using M4
        else if (FUELTYPE === 'M4') {
          //   RSZ <- ifelse(FUELTYPE %in% c("M4"),
          //   .ROScalc(rep("M4", length(FMC)), ISI = ISZ, BUI = NoBUI, FMC, SFC,
          //   PC, PDF100, CC, CBH),
          //   RSZ)
          //   #Eq. 40 (FCFDG 1992) - Surface spread rate with 0 wind upslope for M4
          //   RSF_M4 <- ifelse(FUELTYPE %in% c("M4"), RSZ * SF, RSF_M4)
          //   #Surface spread rate with 0 wind on level ground, using M4
          //   RSZ <- ifelse(FUELTYPE %in% c("M4"),
          //   .ROScalc(rep("D1", length(ISZ)), ISZ, BUI = NoBUI, FMC, SFC, PC,
          //   PDF100, CC, CBH),
          //   RSZ)
          //   #Eq. 40 (FCFDG 1992) - Surface spread rate with 0 wind upslope for D1
          //   RSF_D1 <- ifelse(FUELTYPE %in% c("M4"), RSZ * SF,RSF_D1)
          //   #Eq. 40 (FCFDG 1992) - Surface spread rate with 0 wind upslope for D1
          //   RSF0 <- 1 - (RSF_M4 / a[["M4"]])^(1 / c0[["M4"]])
          //   #Eq. 41a (Wotton 2009) - Calculate the slope equivalent ISI
          //   ISF_M4 <- ifelse(FUELTYPE %in% c("M4") & RSF0 >= 0.01,
          //   log(1 - (RSF_M4 / a[["M4"]])**(1 / c0[["M4"]])) / (-b[["M4"]]),
          //   ISF_M4)
          //   #Eq. 41b (Wotton 2009) - Calculate the slope equivalent ISI
          //   ISF_M4 <- ifelse(FUELTYPE %in% c("M4") & RSF0 < 0.01,
          //   log(0.01) / (-b[["M4"]]),
          //   ISF_M4)
          //   #Eq. 40 (FCFDG 1992) - Surface spread rate with 0 wind upslope for D1
          //   RSF0 <- 1 - (RSF_D1 / a[["D1"]])^(1 / c0[["D1"]])
          //   #Eq. 41a (Wotton 2009) - Calculate the slope equivalent ISI (D1)
          //   ISF_D1 <- ifelse(FUELTYPE %in% c("M4") & RSF0 >= 0.01,
          //   log(1 - (RSF_D1 / a[["D1"]])**(1 / c0[["D1"]])) / (-b[["D1"]]),
          //   ISF_D1)
          //   #Eq. 41b (Wotton 2009) - Calculate the slope equivalent ISI (D1)
          //   ISF_D1 <- ifelse(FUELTYPE %in% c("M4") & RSF0 < 0.01,
          //   log(0.01) / (-b[["D1"]]),
          //   ISF_D1)
          //   #Eq. 42c (Wotton 2009) - Calculate weighted average for the M4 type
          //   ISF <- ifelse(FUELTYPE %in% c("M4"), PDF / 100 * ISF_M4 + (1 - PDF / 100.) *
          //   ISF_D1,
          //   ISF)
          throw Error('slope for M4 not implemented')
        }
        //   #Eqs. 35a, 35b (Wotton 2009) - Curing Factor pivoting around % 58.8
        else if (['O1A', 'O1B'].includes(FUELTYPE)) {
          //   CF <- ifelse(FUELTYPE %in% c("O1A", "O1B"),
          //   ifelse(CC < 58.8, 0.005 * (exp(0.061 * CC) - 1),
          //   0.176 + 0.02 * (CC-58.8)),
          //   CF)
          //   #Eqs. 43a, 43b (Wotton 2009) - slope equivilent ISI for Grass
          //   ISF <- ifelse(FUELTYPE %in% c("O1A", "O1B"),
          //   ifelse((1 - (RSF / (CF * a[FUELTYPE]))**(1 / c0[FUELTYPE])) >= 0.01,
          //   log(1 - (RSF / (CF * a[FUELTYPE]))**(1 / c0[FUELTYPE])) /
          //   (-b[FUELTYPE]),
          //   log(0.01) / (-b[FUELTYPE])),
          //   ISF)
          throw Error('slope for O1A, O1b not implemented')
        }
        //   #Eq. 46 (FCFDG 1992)
        //   m <- 147.2 * (101 - FFMC) / (59.5 + FFMC)
        const m = (147.2 * (101 - FFMC)) / (59.5 + FFMC)
        //   #Eq. 45 (FCFDG 1992) - FFMC function from the ISI equation
        //   fF <- 91.9 * exp(-.1386 * m) * (1 + (m**5.31) / 4.93e7)
        const fF = 91.9 * Math.exp(-0.1386 * m) * (1 + Math.pow(m, 5.31) / 4.93e7)
        //   #Eqs. 44a, 44d (Wotton 2009) - Slope equivalent wind speed
        //   WSE <- 1 / 0.05039 * log(ISF / (0.208 * fF))
        let WSE = (1 / 0.05039) * Math.log(ISF / (0.208 * fF))
        //   #Eqs. 44b, 44e (Wotton 2009) - Slope equivalent wind speed
        //   WSE <- ifelse(WSE > 40 & ISF < (0.999 * 2.496 * fF),
        //   28 - (1 / 0.0818 * log(1 - ISF/ ( 2.496 * fF))),
        //   WSE)
        WSE =
          WSE > 40 && ISF < 0.999 * 2.496 * fF
            ? 28 - (1 / 0.0818) * Math.log(1 - ISF / (2.496 * fF))
            : WSE
        //   #Eqs. 44c (Wotton 2009) - Slope equivalent wind speed
        //   WSE <- ifelse(WSE > 40 & ISF >= (0.999 * 2.496 * fF), 112.45, WSE)
        WSE = WSE > 40 && ISF >= 0.999 * 2.496 * fF ? 112.45 : WSE
        //   #Eq. 47 (FCFDG 1992) - resultant vector magnitude in the x-direction
        //   WSX <- WS * sin(WAZ) + WSE * sin(SAZ)
        const WSX = WS * Math.sin(WAZ) + WSE * Math.sin(SAZ)
        //   #Eq. 48 (FCFDG 1992) - resultant vector magnitude in the y-direction
        //   WSY <- WS * cos(WAZ) + WSE * cos(SAZ)
        const WSY = WS * Math.cos(WAZ) + WSE * Math.cos(SAZ)
        //   #Eq. 49 (FCFDG 1992) - the net effective wind speed
        //   WSV <- sqrt(WSX * WSX + WSY * WSY)
        const WSV = Math.sqrt(WSX * WSX + WSY * WSY)
        //   #stop execution here and return WSV if requested
        //   if (output=="WSV")
        //   return(WSV)
        if (output === 'WSV') {
          return WSV
        }
        //   #Eq. 50 (FCFDG 1992) - the net effective wind direction (radians)
        //   RAZ <- acos(WSY / WSV)
        let RAZ = Math.acos(WSY / WSV)
        //   #Eq. 51 (FCFDG 1992) - convert possible negative RAZ into more understandable
        //   # directions
        //   RAZ <- ifelse(WSX < 0, 2 * pi - RAZ, RAZ)
        RAZ = WSX < 0 ? 2 * Math.PI - RAZ : RAZ
        //   return(RAZ)
        return RAZ
      }

      const eas = layers[0]
      if (eas[0] === 0xff && eas[1] === 0xff && eas[2] === 0xff) {
        // no data - get out of here
        return [0, 0, 0, 0]
      }
      const height = eas[0] === 0xff ? 0xff : eas[0] * 20

      if (height > data.snowLine) {
        return [0, 0, 0, 0]
      }

      const aspect = eas[1] === 0xff ? 0xff : eas[1] * 2
      const slope = eas[2] === 0xff ? 0xff : eas[2] * 2
      const ftl = layers[1]

      // 0xff means no-data
      // the raster should have no values large than 233, and as such the aspect should never
      // be greater than 4671 - but it seems as if some error is introduced by openlayers?
      const heightValid = height !== 0xff && height <= 4671
      // 0xff means no-data
      // the raster should have no values large than 180, and as such the aspect should never
      // be greater than 360 - but it seems as if some error is introduced by openlayers?
      const aspectValid = aspect !== 0xff && aspect <= 360
      const slopeValid = slope !== 0xff

      if (data.mode === 'ROS') {
        try {
          if (height === 0 || height === 0xffffff || height > data.snowLine) {
            return [0, 0, 0, 0]
          } else {
            const ftlNumber = (ftl[0] << 16) | (ftl[1] << 8) | ftl[2]
            if (ftlNumber === 0) {
              return [0, 0, 0, 0]
            }
            const ftlCode = ftlNumberToFtlCode(ftlNumber)
            let ros = -1
            if (ftlCode) {
              const PC = ftlNumber % 100
              const SFC =
                ftlCode === 'C6'
                  ? SFCCalc(ftlCode, data.ffmc, data.bui, PC, undefined)
                  : undefined
              let windSpeed = data.windSpeed
              const aspectValid = aspect !== 0x3ff
              if (data.useNetEffectiveWindSpeed && aspectValid) {
                // console.log('windSpeed', windSpeed)
                const WAZ = data.windAzimuth // Wind Azimuth

                // console.log('ftlCode', ftlCode)
                // console.log('slope', slope)
                // console.log('aspect', aspect)
                // console.log('SFC', SFC)
                // console.log('PC', PC)

                // get the nett effective wind speed
                windSpeed = Slopecalc(
                  ftlCode,
                  data.ffmc,
                  data.bui,
                  windSpeed,
                  WAZ,
                  slope,
                  aspect,
                  data.fmc,
                  SFC,
                  PC,
                  undefined,
                  undefined,
                  data.cbh,
                  undefined,
                  'WSV'
                )
                // console.log('WSV', windSpeed)
                // throw new Error('blah')
                // const slopeEquivalentWindSpeed = calcSlopeEquivalentWindSpeed(ftlNumber, slope)
                // windSpeed = windSpeed += slopeEquivalentWindSpeed
                // if (slopeEquivalentWindSpeed > 0) {
                //   // console.log('slope', slope)
                //   // console.log('slopeEquivalentWindSpeed', slopeEquivalentWindSpeed)
                //   // console.log('windSpeed', windSpeed)
                //   throw new Error('blah')
                // }
              }
              const PDF = undefined
              const CC = undefined
              const isi = ISIcalc(data.ffmc, windSpeed)
              ros = ROScalc(ftlCode, isi, data.bui, data.fmc, SFC, PC, PDF, CC, data.cbh)
              if (ros < 0) {
                // this shouldn't be!
                return [0, 0, 0, 255]
              }
              // if (ftlNumber in data.info['known']) {
              //   data.info['known'][ftlNumber]++
              // } else {
              //   data.info['known'][ftlNumber] = 1
              // }
            } else {
              if (isNonFuel(ftlNumber)) {
                ros = -2
                // if (ftlNumber in data.info['known']) {
                //   data.info['known'][ftlNumber]++
                // } else {
                //   data.info['known'][ftlNumber] = 1
                // }
              } else {
                // if (ftlNumber in data.info['unknown']) {
                //   data.info['unknown'][ftlNumber]++
                // } else {
                //   data.info['unknown'][ftlNumber] = 1
                // }
                return [0, 0, 0, 255]
              }
            }

            if (ros > data.maxRos) {
              data.maxRos = ros
              // console.log('max ros:', ros)
            }
            return calcROSColour(ros, data.opacity)
          }
        } catch (e) {
          return [0, 0, 0, 255]
        }
      } else if (data.mode === 'Elevation') {
        if (!heightValid) {
          return [0, 0, 0, 0]
        }
        const adjustedHeight = Math.round(Math.min(255, (height / 2500) * 255))
        return [adjustedHeight, adjustedHeight, adjustedHeight, data.opacity]
      } else if (data.mode === 'Aspect') {
        if (!aspectValid) {
          return [0, 0, 0, 0]
        }
        const adjustedAspect = Math.round(Math.min(255, (aspect / 360) * 255))
        return [adjustedAspect, adjustedAspect, adjustedAspect, data.opacity]
      } else if (data.mode === 'Slope') {
        if (!slopeValid) {
          return [0, 0, 0, 0]
        }
        const adjustedSlope = Math.round(Math.min(255, (slope / 100) * 255))
        return [adjustedSlope, adjustedSlope, adjustedSlope, data.opacity]
      }
      return [0, 0, 0, 0]
    },
    lib: {}
  })
  raster.on('beforeoperations', function(event) {
    event.data.opacity = raster.get('opacity')
    event.data.snowLine = raster.get('snowLine')
    event.data.bui = raster.get('bui')
    event.data.ffmc = raster.get('ffmc')
    event.data.fmc = raster.get('fmc')
    event.data.cbh = raster.get('cbh')
    event.data.windSpeed = raster.get('windSpeed')
    event.data.windAzimuth = raster.get('windAzimuth')
    event.data.useNetEffectiveWindSpeed = raster.get('useNetEffectiveWindSpeed')
    event.data.mode = raster.get('mode')
    // event.data.info = raster.get('info')
    event.data.maxRos = 0
  })
  raster.on('afteroperations', function(event) {
    console.log('after')
    // if (event.data.info) {
    //   console.log('maxros', event.data.maxRos)
    //   // console.log('known:')
    //   // for (let key in event.data.info['known']) {
    //   //   console.log(`${key}: ${event.data.info['known'][key]}`)
    //   // }
    //   console.log('unknown:')
    //   for (let key in event.data.info['unknown']) {
    //     console.log(`${key}: ${event.data.info['unknown'][key]}`)
    //   }
    // }
  })
  return raster
}
interface Props {
  snowLine: number
  bui: number
  ffmc: number
  fmc: number
  cbh: number
  windSpeed: number
  windAzimuth: number
  useNetEffectiveWindSpeed: boolean
  opacity: number
  mode: string
}

const RateOfSpreadMap = ({
  snowLine,
  bui,
  ffmc,
  fmc,
  cbh,
  windSpeed,
  windAzimuth,
  useNetEffectiveWindSpeed,
  mode,
  opacity
}: Props) => {
  const [center, setCenter] = useState(fromLonLat(CENTER_OF_BC))
  const [raster, setRaster] = useState<olSource.Raster | undefined>(undefined)

  useEffect(() => {
    console.log('useEffect []')
    setRaster(createRaster())
  }, [])

  useEffect(() => {
    if (raster) {
      raster.set('snowLine', snowLine)
      raster.set('bui', bui)
      raster.set('ffmc', ffmc)
      raster.set('fmc', fmc)
      raster.set('cbh', cbh)
      raster.set('windSpeed', windSpeed)
      raster.set('windAzimuth', windAzimuth)
      raster.set('useNetEffectiveWindSpeed', useNetEffectiveWindSpeed)
      raster.set('opacity', opacity)
      raster.set('mode', mode)
      raster.changed()
    }
  }, [
    snowLine,
    bui,
    ffmc,
    fmc,
    cbh,
    windSpeed,
    windAzimuth,
    useNetEffectiveWindSpeed,
    opacity,
    mode,
    raster
  ])

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
      {/* <TileLayer source={easSource} /> */}
      <TileLayer source={source} />
      {raster && <ImageLayer source={raster} />}
    </Map>
  )
}

export default React.memo(RateOfSpreadMap)
