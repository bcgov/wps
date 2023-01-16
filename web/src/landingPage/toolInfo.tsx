import React from 'react'
import AirOutlinedIcon from '@mui/icons-material/AirOutlined'
import CalculateOutlinedIcon from '@mui/icons-material/CalculateOutlined'
import LocalFireDepartmentIcon from '@mui/icons-material/LocalFireDepartment'
import PercentIcon from '@mui/icons-material/Percent'
import PublicIcon from '@mui/icons-material/Public'
import WhatshotOutlinedIcon from '@mui/icons-material/WhatshotOutlined'
import {
  C_HAINES_NAME,
  C_HAINES_ROUTE,
  FIRE_BEHAVIOUR_ADVISORY_NAME,
  FIRE_BEHAVIOUR_ADVISORY_ROUTE,
  FIRE_BEHAVIOUR_CALC_NAME,
  FIRE_BEHAVIOR_CALC_ROUTE,
  HFI_CALC_NAME,
  HFI_CALC_ROUTE,
  MORE_CAST_NAME,
  MORECAST_ROUTE,
  PERCENTILE_CALC_NAME,
  PERCENTILE_CALC_ROUTE
} from 'utils/constants'

const ICON_FONT_SIZE = 'large'
interface ToolInfo {
  name: string
  route: string
  description: React.ReactNode | string
  icon: React.ReactNode
  isBeta: boolean
}

export const fireBehaviourAdvisoryInfo: ToolInfo = {
  name: FIRE_BEHAVIOUR_ADVISORY_NAME,
  route: FIRE_BEHAVIOUR_ADVISORY_ROUTE,
  description:
    'A spatial analysis that automates the continuous monitoring, updating, and communication of anticipated fire behaviour that will challenge direct suppression efforts and put the safety of responders at risk.',
  icon: <LocalFireDepartmentIcon color="primary" fontSize={ICON_FONT_SIZE} />,
  isBeta: true
}

export const cHainesInfo: ToolInfo = {
  name: C_HAINES_NAME,
  route: C_HAINES_ROUTE,
  description:
    'A provincial map that animates forecasted atmospheric stability and potential for pyro-convection in the form of the Continuous Haines Index.',
  icon: <PublicIcon color="primary" fontSize={ICON_FONT_SIZE} />,
  isBeta: false
}

export const fireBehaviourCalcInfo: ToolInfo = {
  name: FIRE_BEHAVIOUR_CALC_NAME,
  route: FIRE_BEHAVIOR_CALC_ROUTE,
  description:
    'A mobile application for calculating fire behaviour in the field. Available for downloasd from the Apple and Google Play stores.',
  icon: <WhatshotOutlinedIcon color="primary" fontSize={ICON_FONT_SIZE} />,
  isBeta: false
}

export const hfiCalcInfo: ToolInfo = {
  name: HFI_CALC_NAME,
  route: HFI_CALC_ROUTE,
  description:
    'A tool that supports the calculation of fire behaviour metrics given forecast or actual weather conditions and user-specified fuel types.',
  icon: <CalculateOutlinedIcon color="primary" fontSize={ICON_FONT_SIZE} />,
  isBeta: false
}

export const moreCastInfo: ToolInfo = {
  name: MORE_CAST_NAME,
  route: MORECAST_ROUTE,
  description:
    'A system that skill scores numerical weather models and enables selection, bias correction, and integration of weather forecast information with others applications.',
  icon: <AirOutlinedIcon color="primary" fontSize={ICON_FONT_SIZE} />,
  isBeta: true
}

export const percentileCalcInfo: ToolInfo = {
  name: PERCENTILE_CALC_NAME,
  route: PERCENTILE_CALC_ROUTE,
  description:
    'A tool that helps users identify fire weather indices coinciding with historically uncommon fire danger at weather stations located around the province.',  
  icon: <PercentIcon color="primary" fontSize={ICON_FONT_SIZE} />,
  isBeta: false
}

// The order of items in this array determines the order of items as they appear in the landing page
// side bar and order of CardTravelSharp.
export const toolInfos = [
  fireBehaviourAdvisoryInfo,
  moreCastInfo,
  cHainesInfo,
  fireBehaviourCalcInfo,
  hfiCalcInfo,
  percentileCalcInfo
]
