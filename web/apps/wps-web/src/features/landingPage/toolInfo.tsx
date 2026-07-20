import AirOutlinedIcon from '@mui/icons-material/AirOutlined'
import BorderAllIcon from '@mui/icons-material/BorderAll'
import CalculateOutlinedIcon from '@mui/icons-material/CalculateOutlined'
import LocalFireDepartmentIcon from '@mui/icons-material/LocalFireDepartment'
import PercentIcon from '@mui/icons-material/Percent'
import TravelExploreOutlinedIcon from '@mui/icons-material/TravelExploreOutlined'
import WatchIcon from '@mui/icons-material/Watch'
import WhatshotIcon from '@mui/icons-material/Whatshot'
import WhatshotOutlinedIcon from '@mui/icons-material/WhatshotOutlined'
import Box from '@mui/material/Box'
import Link from '@mui/material/Link'
import Typography from '@mui/material/Typography'
import {
  FBP_GO_NAME,
  FBP_GO_ROUTE,
  FIRE_BEHAVIOR_CALC_ROUTE,
  FIRE_BEHAVIOUR_ADVISORY_NAME,
  FIRE_BEHAVIOUR_ADVISORY_ROUTE,
  FIRE_BEHAVIOUR_CALC_NAME,
  FIRE_WATCH_NAME,
  FIRE_WATCH_ROUTE,
  HFI_CALC_NAME,
  HFI_CALC_ROUTE,
  MORE_CAST_NAME,
  MORECAST_ROUTE,
  PERCENTILE_CALC_NAME,
  PERCENTILE_CALC_ROUTE,
  SFMS_INSIGHTS_NAME,
  SFMS_INSIGHTS_ROUTE,
  WEATHER_TOOLKIT_NAME,
  WEATHER_TOOLKIT_ROUTE
} from '@wps/utils/constants'
import type React from 'react'

const ICON_FONT_SIZE = 'large'
const PREDICTIVE_SERVICES_UNIT = 'Predictive Services Unit'
export const BCPS_TOOL_ICON_COLOUR = '#ea580c'
export const PUBLIC_TOOL_ICON_COLOUR = '#0d9488'

export interface ToolInfo {
  name: string
  route: string
  subheading: string
  description: React.ReactNode | string
  icon: React.ReactNode
  isBeta: boolean
  managedBy: string
  isExternal?: boolean
}

export const fireBehaviourAdvisoryInfo: ToolInfo = {
  name: FIRE_BEHAVIOUR_ADVISORY_NAME,
  route: FIRE_BEHAVIOUR_ADVISORY_ROUTE,
  subheading: 'Provincial Fire Behaviour Advisories',
  description: (
    <Typography>
      A spatial analysis tool that automates the continuous monitoring, updating, and communication of anticipated fire
      behaviour that will challenge direct suppression efforts and put the safety of responders at risk.
      <br />
      Available for download from the&nbsp;
      <Link href="https://apps.apple.com/us/app/asa-go/id6741596129" rel="noreferrer" target="_blank">
        Apple
      </Link>
      &nbsp;and&nbsp;
      <Link href="https://play.google.com/store/apps/details?id=ca.bc.gov.asago" rel="noreferrer" target="_blank">
        Google Play
      </Link>
      &nbsp;stores.
    </Typography>
  ),
  icon: <LocalFireDepartmentIcon fontSize={ICON_FONT_SIZE} htmlColor={BCPS_TOOL_ICON_COLOUR} />,
  isBeta: false,
  managedBy: PREDICTIVE_SERVICES_UNIT
}

export const fireBehaviourCalcInfo: ToolInfo = {
  name: FIRE_BEHAVIOUR_CALC_NAME,
  route: FIRE_BEHAVIOR_CALC_ROUTE,
  subheading: 'Fire Behaviour Calculator',
  description: (
    <Typography>
      A tool that supports the calculation of fire behaviour metrics given forecast or actual weather conditions and
      user-specified fuel types.
    </Typography>
  ),
  icon: <WhatshotOutlinedIcon fontSize={ICON_FONT_SIZE} htmlColor={BCPS_TOOL_ICON_COLOUR} />,
  isBeta: false,
  managedBy: PREDICTIVE_SERVICES_UNIT
}

export const hfiCalcInfo: ToolInfo = {
  name: HFI_CALC_NAME,
  route: HFI_CALC_ROUTE,
  subheading: 'Head Fire Intensity Calculator',
  description: (
    <Typography>
      An application that informs preparedness levels throughout the province based on anticipated head fire intensities
      and fire occurrence.
    </Typography>
  ),
  icon: <CalculateOutlinedIcon fontSize={ICON_FONT_SIZE} htmlColor={BCPS_TOOL_ICON_COLOUR} />,
  isBeta: false,
  managedBy: PREDICTIVE_SERVICES_UNIT
}

export const moreCastInfo: ToolInfo = {
  name: MORE_CAST_NAME,
  route: MORECAST_ROUTE,
  subheading: 'Weather Models and Forecasting',
  description: (
    <Typography>
      A system that enhances how the predictive services team creates weather forecasts and integrates this information
      with other applications.
    </Typography>
  ),
  icon: <AirOutlinedIcon fontSize={ICON_FONT_SIZE} htmlColor={BCPS_TOOL_ICON_COLOUR} />,
  isBeta: false,
  managedBy: PREDICTIVE_SERVICES_UNIT
}

export const percentileCalcInfo: ToolInfo = {
  name: PERCENTILE_CALC_NAME,
  route: PERCENTILE_CALC_ROUTE,
  subheading: 'Historical fire weather percentile comparisons',
  description: (
    <Typography>
      A tool that helps users identify fire weather indices coinciding with historically uncommon fire danger at weather
      stations located around the province.
    </Typography>
  ),
  icon: <PercentIcon fontSize={ICON_FONT_SIZE} htmlColor={PUBLIC_TOOL_ICON_COLOUR} />,
  isBeta: false,
  managedBy: PREDICTIVE_SERVICES_UNIT
}

export const fbpGoInfo: ToolInfo = {
  name: FBP_GO_NAME,
  route: FBP_GO_ROUTE,
  subheading: 'Mobile fire behaviour calculations for field use',
  description: (
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
  ),
  icon: <img alt="FBP Go logo" style={{ height: '36px', width: '36px' }} src="/images/fbpgo_maskable.png" />,
  isBeta: false,
  managedBy: PREDICTIVE_SERVICES_UNIT
}

export const sfmsInsightsInfo: ToolInfo = {
  name: SFMS_INSIGHTS_NAME,
  route: SFMS_INSIGHTS_ROUTE,
  subheading: 'Map-based wildfire data exploration',
  description: (
    <Typography>
      A visualization tool providing an interactive map-based interface to analyze and understand critical
      wildfire-related data.
    </Typography>
  ),
  icon: <TravelExploreOutlinedIcon fontSize={ICON_FONT_SIZE} htmlColor={BCPS_TOOL_ICON_COLOUR} />,
  isBeta: true,
  managedBy: PREDICTIVE_SERVICES_UNIT
}

export const fireWatchInfo: ToolInfo = {
  name: FIRE_WATCH_NAME,
  route: FIRE_WATCH_ROUTE,
  subheading: 'Ten-day watch conditions for fire weather and behaviour',
  description: (
    <Typography>
      A heads up application that indicates when specified fire weather and fire behaviour could occur over the next ten
      days.
    </Typography>
  ),
  icon: (
    <Box
      sx={{
        display: 'flex',
        position: 'relative'
      }}
    >
      <WatchIcon sx={{ fontSize: 40 }} htmlColor={BCPS_TOOL_ICON_COLOUR} />
      <WhatshotIcon
        htmlColor={BCPS_TOOL_ICON_COLOUR}
        sx={{
          fontSize: 16,
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          pointerEvents: 'none'
        }}
      />
    </Box>
  ),
  isBeta: true,
  managedBy: PREDICTIVE_SERVICES_UNIT
}

export const weatherToolkitInfo: ToolInfo = {
  name: WEATHER_TOOLKIT_NAME,
  route: WEATHER_TOOLKIT_ROUTE,
  subheading: 'GDPS and RDPS chart visualization',
  description: <Typography>A tool for visualizing GDPS and RDPS 4-Panel Charts.</Typography>,
  icon: <BorderAllIcon fontSize={ICON_FONT_SIZE} htmlColor={PUBLIC_TOOL_ICON_COLOUR} />,
  isBeta: true,
  managedBy: PREDICTIVE_SERVICES_UNIT
}

// The order of items in this array determines their order in the landing page sections and quick access menu.
export const toolInfos = [
  fireBehaviourAdvisoryInfo,
  moreCastInfo,
  hfiCalcInfo,
  fbpGoInfo,
  fireBehaviourCalcInfo,
  fireWatchInfo,
  sfmsInsightsInfo,
  percentileCalcInfo,
  weatherToolkitInfo
]
