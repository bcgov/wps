import AirOutlinedIcon from '@mui/icons-material/AirOutlined'
import BorderAllIcon from '@mui/icons-material/BorderAll'
import CalculateOutlinedIcon from '@mui/icons-material/CalculateOutlined'
import PercentIcon from '@mui/icons-material/Percent'
import TravelExploreOutlinedIcon from '@mui/icons-material/TravelExploreOutlined'
import WatchIcon from '@mui/icons-material/Watch'
import WhatshotIcon from '@mui/icons-material/Whatshot'
import WhatshotOutlinedIcon from '@mui/icons-material/WhatshotOutlined'
import Box from '@mui/material/Box'
import Link from '@mui/material/Link'
import Typography from '@mui/material/Typography'
import { PUBLIC_TOOL_ICON_COLOUR, theme } from '@wps/ui/theme'
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
import { CSBC_PREDICTIVE_SERVICES_MANAGED_BY, type ManagedByInfo } from './managedBy'

const ICON_FONT_SIZE = 'large'

export interface ToolInfo {
  name: string
  route: string
  description: React.ReactNode | string
  icon: React.ReactNode
  isBeta: boolean
  managedBy: ManagedByInfo
  isExternal?: boolean
}

export const fireBehaviourAdvisoryInfo: ToolInfo = {
  name: FIRE_BEHAVIOUR_ADVISORY_NAME,
  route: FIRE_BEHAVIOUR_ADVISORY_ROUTE,
  description: (
    <Typography>
      An app for BC Wildland Firefighters that automates the continuous monitoring, updating, and communication of
      anticipated fire behaviour.
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
  icon: (
    <img
      alt={`${FIRE_BEHAVIOUR_ADVISORY_NAME} logo`}
      src="/images/asa-go-logo.png"
      style={{ height: '100%', objectFit: 'cover', width: '100%' }}
    />
  ),
  isBeta: false,
  managedBy: CSBC_PREDICTIVE_SERVICES_MANAGED_BY
}

export const fireBehaviourCalcInfo: ToolInfo = {
  name: FIRE_BEHAVIOUR_CALC_NAME,
  route: FIRE_BEHAVIOR_CALC_ROUTE,
  description: (
    <Typography>
      Supports the calculation of fire behaviour metrics given forecast or actual weather conditions and user-specified
      fuel types.
    </Typography>
  ),
  icon: <WhatshotOutlinedIcon fontSize={ICON_FONT_SIZE} htmlColor={theme.palette.primary.main} />,
  isBeta: false,
  managedBy: CSBC_PREDICTIVE_SERVICES_MANAGED_BY
}

export const hfiCalcInfo: ToolInfo = {
  name: HFI_CALC_NAME,
  route: HFI_CALC_ROUTE,
  description: (
    <Typography>
      Informs preparedness levels throughout the province based on anticipated head fire intensities and fire
      occurrence.
    </Typography>
  ),
  icon: <CalculateOutlinedIcon fontSize={ICON_FONT_SIZE} htmlColor={theme.palette.primary.main} />,
  isBeta: false,
  managedBy: CSBC_PREDICTIVE_SERVICES_MANAGED_BY
}

export const moreCastInfo: ToolInfo = {
  name: MORE_CAST_NAME,
  route: MORECAST_ROUTE,
  description: (
    <Typography>
      Enhances how the predictive services team creates weather forecasts and integrates this information with other
      applications.
    </Typography>
  ),
  icon: <AirOutlinedIcon fontSize={ICON_FONT_SIZE} htmlColor={theme.palette.primary.main} />,
  isBeta: false,
  managedBy: CSBC_PREDICTIVE_SERVICES_MANAGED_BY
}

export const percentileCalcInfo: ToolInfo = {
  name: PERCENTILE_CALC_NAME,
  route: PERCENTILE_CALC_ROUTE,
  description: (
    <Typography>
      Helps users identify fire weather indices coinciding with historically uncommon fire danger at weather stations
      located around the province.
    </Typography>
  ),
  icon: <PercentIcon fontSize={ICON_FONT_SIZE} htmlColor={PUBLIC_TOOL_ICON_COLOUR} />,
  isBeta: false,
  managedBy: CSBC_PREDICTIVE_SERVICES_MANAGED_BY
}

export const fbpGoInfo: ToolInfo = {
  name: FBP_GO_NAME,
  route: FBP_GO_ROUTE,
  description: (
    <Typography>
      Calculates fire behaviour in the field. Available for download from the&nbsp;
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
  managedBy: CSBC_PREDICTIVE_SERVICES_MANAGED_BY
}

export const sfmsInsightsInfo: ToolInfo = {
  name: SFMS_INSIGHTS_NAME,
  route: SFMS_INSIGHTS_ROUTE,
  description: (
    <Typography>
      Provides an interactive map-based interface to analyze and understand critical wildfire-related data.
    </Typography>
  ),
  icon: <TravelExploreOutlinedIcon fontSize={ICON_FONT_SIZE} htmlColor={theme.palette.primary.main} />,
  isBeta: true,
  managedBy: CSBC_PREDICTIVE_SERVICES_MANAGED_BY
}

export const fireWatchInfo: ToolInfo = {
  name: FIRE_WATCH_NAME,
  route: FIRE_WATCH_ROUTE,
  description: (
    <Typography>
      Indicates when specified fire weather and fire behaviour could occur over the next ten days.
    </Typography>
  ),
  icon: (
    <Box
      sx={{
        display: 'flex',
        position: 'relative'
      }}
    >
      <WatchIcon sx={{ fontSize: 40 }} htmlColor={theme.palette.primary.main} />
      <WhatshotIcon
        htmlColor={theme.palette.primary.main}
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
  managedBy: CSBC_PREDICTIVE_SERVICES_MANAGED_BY
}

export const weatherToolkitInfo: ToolInfo = {
  name: WEATHER_TOOLKIT_NAME,
  route: WEATHER_TOOLKIT_ROUTE,
  description: <Typography>A tool for visualizing GDPS and RDPS 4-Panel Charts.</Typography>,
  icon: <BorderAllIcon fontSize={ICON_FONT_SIZE} htmlColor={PUBLIC_TOOL_ICON_COLOUR} />,
  isBeta: true,
  managedBy: CSBC_PREDICTIVE_SERVICES_MANAGED_BY
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
