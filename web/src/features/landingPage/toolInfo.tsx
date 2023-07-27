import React from 'react'
import AirOutlinedIcon from '@mui/icons-material/AirOutlined'
import CalculateOutlinedIcon from '@mui/icons-material/CalculateOutlined'
import LocalFireDepartmentIcon from '@mui/icons-material/LocalFireDepartment'
import PercentIcon from '@mui/icons-material/Percent'
import PublicIcon from '@mui/icons-material/Public'
import WhatshotOutlinedIcon from '@mui/icons-material/WhatshotOutlined'
import Link from '@mui/material/Link'
import Typography from '@mui/material/Typography'

import {
  C_HAINES_NAME,
  C_HAINES_ROUTE,
  FBP_GO_NAME,
  FBP_GO_ROUTE,
  FIRE_BEHAVIOUR_ADVISORY_NAME,
  FIRE_BEHAVIOUR_ADVISORY_ROUTE,
  FIRE_BEHAVIOUR_CALC_NAME,
  FIRE_BEHAVIOR_CALC_ROUTE,
  HFI_CALC_NAME,
  HFI_CALC_ROUTE,
  MORE_CAST_NAME,
  MORECAST_ROUTE,
  PERCENTILE_CALC_NAME,
  PERCENTILE_CALC_ROUTE,
  MORE_CAST_2_NAME,
  MORE_CAST_2_ROUTE
} from 'utils/constants'

const ICON_FONT_SIZE = 'large'
export interface ToolInfo {
  name: string
  route: string
  description: React.ReactNode | string
  icon: React.ReactNode
  isBeta: boolean
}

export const fireBehaviourAdvisoryInfo: ToolInfo = {
  name: FIRE_BEHAVIOUR_ADVISORY_NAME,
  route: FIRE_BEHAVIOUR_ADVISORY_ROUTE,
  description: (
    <Typography>
      A spatial analysis tool that automates the continuous monitoring, updating, and communication of anticipated fire
      behaviour that will challenge direct suppression efforts and put the safety of responders at risk.
    </Typography>
  ),
  icon: <LocalFireDepartmentIcon color="primary" fontSize={ICON_FONT_SIZE} />,
  isBeta: true
}

export const cHainesInfo: ToolInfo = {
  name: C_HAINES_NAME,
  route: C_HAINES_ROUTE,
  description: (
    <Typography>
      A provincial map that animates forecasted atmospheric stability and potential for pyro-convection in the form of
      the Continuous Haines Index.
    </Typography>
  ),
  icon: <PublicIcon color="primary" fontSize={ICON_FONT_SIZE} />,
  isBeta: false
}

export const fireBehaviourCalcInfo: ToolInfo = {
  name: FIRE_BEHAVIOUR_CALC_NAME,
  route: FIRE_BEHAVIOR_CALC_ROUTE,
  description: (
    <Typography>
      A tool that supports the calculation of fire behaviour metrics given forecast or actual weather conditions and
      user-specified fuel types.
    </Typography>
  ),
  icon: <WhatshotOutlinedIcon color="primary" fontSize={ICON_FONT_SIZE} />,
  isBeta: false
}

export const hfiCalcInfo: ToolInfo = {
  name: HFI_CALC_NAME,
  route: HFI_CALC_ROUTE,
  description: (
    <Typography>
      An application that informs preparedness levels throughout the province based on anticipated head fire intensities
      and fire occurrence.
    </Typography>
  ),
  icon: <CalculateOutlinedIcon color="primary" fontSize={ICON_FONT_SIZE} />,
  isBeta: false
}

export const moreCastInfo: ToolInfo = {
  name: MORE_CAST_NAME,
  route: MORECAST_ROUTE,
  description: (
    <Typography>
      A system that uses weather station observations to skill score temperature and relative humidity values forecasted
      by three numerical weather models.
    </Typography>
  ),
  icon: <AirOutlinedIcon color="primary" fontSize={ICON_FONT_SIZE} />,
  isBeta: true
}

export const moreCast2Info: ToolInfo = {
  name: MORE_CAST_2_NAME,
  route: MORE_CAST_2_ROUTE,
  description: (
    <Typography>
      A system that enhances how the predictive services team creates weather forecasts and integrates this information
      with other applications.
    </Typography>
  ),
  icon: <AirOutlinedIcon color="primary" fontSize={ICON_FONT_SIZE} />,
  isBeta: true
}

export const percentileCalcInfo: ToolInfo = {
  name: PERCENTILE_CALC_NAME,
  route: PERCENTILE_CALC_ROUTE,
  description: (
    <Typography>
      A tool that helps users identify fire weather indices coinciding with historically uncommon fire danger at weather
      stations located around the province.
    </Typography>
  ),
  icon: <PercentIcon color="primary" fontSize={ICON_FONT_SIZE} />,
  isBeta: false
}

export const fbpGoInfo: ToolInfo = {
  name: FBP_GO_NAME,
  route: FBP_GO_ROUTE,
  description: (
    <>
      <Typography>
        A mobile application for calculating fire behaviour in the field. Available for download from the&nbsp;
        <Link href="https://apps.apple.com/app/fbp-go/id1605675034" rel="noreferrer" target="_blank">
          Apple
        </Link>
        &nbsp;and&nbsp;
        <Link href="https://play.google.com/store/apps/details?id=ca.bc.gov.FBPGo" rel="noreferrer" target="_blank">
          Google Play
        </Link>
        &nbsp;stores.
      </Typography>
    </>
  ),
  icon: <img style={{ height: '36px', width: '36px' }} src="/images/fbpgo_maskable.png" />,
  isBeta: false
}

// The order of items in this array determines the order of items as they appear in the landing page
// side bar and order of CardTravelSharp.
// Temporarily exclude MoreCast 2.0 from prod
export const toolInfos = [
  moreCast2Info,
  fireBehaviourAdvisoryInfo,
  moreCastInfo,
  cHainesInfo,
  fireBehaviourCalcInfo,
  hfiCalcInfo,
  percentileCalcInfo,
  fbpGoInfo
]
