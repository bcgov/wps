import { BEcalc } from 'utils/cffdrs/BEcalc'
import { CFBcalc } from 'utils/cffdrs/CFBcalc'

export function C6calc(
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
): number {
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
