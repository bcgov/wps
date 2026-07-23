import AreaChartOutlinedIcon from '@mui/icons-material/AreaChartOutlined'
import CellTowerIcon from '@mui/icons-material/CellTower'
import ThermostatOutlinedIcon from '@mui/icons-material/ThermostatOutlined'
import Link from '@mui/material/Link'
import Typography from '@mui/material/Typography'
import { API_ACCESS_COLOUR, PUBLIC_TOOL_ICON_COLOUR } from '@wps/ui/theme'
import { BCWS_PREDICTIVE_SERVICES_MANAGED_BY, CSBC_PREDICTIVE_SERVICES_MANAGED_BY } from './managedBy'
import type { ToolInfo } from './toolInfo'

export const SFMS_DAILY_FIRE_WEATHER_INDEX_ROUTE = 'https://api.gov.bc.ca/devportal/api-directory/4336'
export const WX_DATA_VIEWER_ROUTE = 'https://huggingface.co/spaces/ssidds/WX_data_viewer'
export const WX_WEATHER_ALERTS_ROUTE = 'https://riodeoro.github.io/wx-network-alerts/'

export const sfmsDailyFireWeatherIndexInfo: ToolInfo = {
  name: 'SFMS Fire Weather Index',
  route: SFMS_DAILY_FIRE_WEATHER_INDEX_ROUTE,
  section: 'api',
  description: (
    <Typography>
      Access the SFMS Fire Weather Index API through the API Services Portal. The available data can be viewed{' '}
      <Link href="https://wfapps.nrs.gov.bc.ca/pub/wfwx-info-war/sfms" rel="noreferrer" target="_blank">
        here
      </Link>
      .
    </Typography>
  ),
  icon: <ThermostatOutlinedIcon fontSize="large" htmlColor={API_ACCESS_COLOUR} />,
  isBeta: false,
  managedBy: CSBC_PREDICTIVE_SERVICES_MANAGED_BY,
  isExternal: true
}

export const wxDataViewerInfo: ToolInfo = {
  name: 'WX Data Viewer',
  route: WX_DATA_VIEWER_ROUTE,
  section: 'public',
  description: (
    <Typography>
      A near real time and historical hourly visualizer of BCWS weather station data. Plots actuals and climatology,
      produces wind and initial spread index roses, performs spread analysis, and calculates risk landscape polygons.
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
  section: 'public',
  description: (
    <Typography>A dashboard to visualize and monitor sensor performance using hourly weather observations.</Typography>
  ),
  icon: <CellTowerIcon fontSize="large" htmlColor={PUBLIC_TOOL_ICON_COLOUR} />,
  isBeta: false,
  managedBy: BCWS_PREDICTIVE_SERVICES_MANAGED_BY,
  isExternal: true
}

export const externalToolInfos = [wxDataViewerInfo, wxWeatherAlertsInfo, sfmsDailyFireWeatherIndexInfo]
