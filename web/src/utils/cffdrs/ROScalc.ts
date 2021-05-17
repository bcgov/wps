import { C6calc } from 'utils/cffdrs/C6calc'
import { BEcalc } from 'utils/cffdrs/BEcalc'

export function ROScalc(
  FUELTYPE: string,
  ISI: number,
  BUI: number,
  FMC: number,
  SFC: number | undefined = undefined,
  PC: number | undefined = undefined,
  PDF: number | undefined = undefined,
  CC: number | undefined = undefined,
  CBH: number
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
      ((0.2 * (100 - PC)) / 100) * ROScalc('D1', ISI, NoBUI, FMC, SFC, PC, PDF, CC, CBH)
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
      throw 'CC not specified'
    }
    const CF = CC < 58.8 ? 0.005 * (Math.exp(0.061 * CC) - 1) : 0.176 + 0.02 * (CC - 58.8)
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
