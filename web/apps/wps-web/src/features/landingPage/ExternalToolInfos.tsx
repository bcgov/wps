import AreaChartOutlinedIcon from '@mui/icons-material/AreaChartOutlined'
import CellTowerIcon from '@mui/icons-material/CellTower'
import ThermostatOutlinedIcon from '@mui/icons-material/ThermostatOutlined'
import Link from '@mui/material/Link'
import Typography from '@mui/material/Typography'
import { API_ACCESS_COLOUR, PUBLIC_TOOL_ICON_COLOUR } from '@wps/ui/theme'
import { BCWS_PREDICTIVE_SERVICES_MANAGED_BY, CSBC_PREDICTIVE_SERVICES_MANAGED_BY } from './managedBy'
import type { ToolInfo } from './toolInfo'

export const SFMS_API_ROUTE = 'https://api.gov.bc.ca/devportal/api-directory/4445'
export const WX_DATA_VIEWER_ROUTE = 'https://huggingface.co/spaces/ssidds/WX_data_viewer'
export const WX_NETWORK_ALERTS_ROUTE = 'https://riodeoro.github.io/wx-network-alerts/'

export const sfmsApiInfo: ToolInfo = {
  name: 'SFMS API',
  route: SFMS_API_ROUTE,
  section: 'api',
  description: (
    <Typography>
      Access daily fire weather indices, fire behaviour predictions, and weather inputs from the Spatial Fire Management
      System. Download rasters or sample values at a point for actuals and forecasts. Request an API key through the API
      Services Portal. View the{' '}
      <Link href="https://psu.api.gov.bc.ca/api/docs" rel="noreferrer" target="_blank">
        API documentation
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

export const wxNetworkAlertsInfo: ToolInfo = {
  name: 'WX Network Alerts',
  route: WX_NETWORK_ALERTS_ROUTE,
  section: 'public',
  description: (
    <Typography>A dashboard to visualize and monitor sensor performance using hourly weather observations.</Typography>
  ),
  icon: <CellTowerIcon fontSize="large" htmlColor={PUBLIC_TOOL_ICON_COLOUR} />,
  isBeta: false,
  managedBy: BCWS_PREDICTIVE_SERVICES_MANAGED_BY,
  isExternal: true
}

export const externalToolInfos = [wxDataViewerInfo, wxNetworkAlertsInfo, sfmsApiInfo]
