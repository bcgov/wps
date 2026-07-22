import AreaChartOutlinedIcon from '@mui/icons-material/AreaChartOutlined'
import CellTowerIcon from '@mui/icons-material/CellTower'
import Typography from '@mui/material/Typography'
import { BCWS_PREDICTIVE_SERVICES_MANAGED_BY, type ToolInfo } from 'features/landingPage/toolInfo'
import { PUBLIC_TOOL_ICON_COLOUR } from './landingPageConfig'

export const WX_DATA_VIEWER_ROUTE = 'https://huggingface.co/spaces/ssidds/WX_data_viewer'
export const WX_WEATHER_ALERTS_ROUTE = 'https://riodeoro.github.io/wx-network-alerts/'

export const wxDataViewerInfo: ToolInfo = {
  name: 'WX Data Viewer',
  route: WX_DATA_VIEWER_ROUTE,
  description: (
    <Typography>
      A near real time and historical hourly visualizer of BCWS weather station data. Plots actuals and climatology,
      performs spread analysis, and calculates risk landscape polygons.
    </Typography>
  ),
  icon: <AreaChartOutlinedIcon fontSize="large" htmlColor={PUBLIC_TOOL_ICON_COLOUR} />,
  isBeta: false,
  managedBy: BCWS_PREDICTIVE_SERVICES_MANAGED_BY,
  isExternal: true
}

export const wxWeatherAlertsInfo: ToolInfo = {
  name: 'WX Weather Alerts',
  route: WX_WEATHER_ALERTS_ROUTE,
  description: (
    <Typography>A dashboard to visualize and monitor sensor performance using hourly weather observations.</Typography>
  ),
  icon: <CellTowerIcon fontSize="large" htmlColor={PUBLIC_TOOL_ICON_COLOUR} />,
  isBeta: false,
  managedBy: BCWS_PREDICTIVE_SERVICES_MANAGED_BY,
  isExternal: true
}

export const externalToolInfos = [wxDataViewerInfo, wxWeatherAlertsInfo]
