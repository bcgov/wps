import AirOutlinedIcon from '@mui/icons-material/AirOutlined'
import Typography from '@mui/material/Typography'
import type { ToolInfo } from 'features/landingPage/toolInfo'

export const WX_DATA_VIEWER_ROUTE = 'https://huggingface.co/spaces/ssidds/WX_data_viewer'
export const WX_DATA_VIEWER_MANAGING_TEAM = 'TBD'

export const wxDataViewerInfo: ToolInfo = {
  name: 'WX Data Viewer',
  route: WX_DATA_VIEWER_ROUTE,
  description: (
    <Typography>
      A near real time (-1 day) and historical hourly visualizer of BCWS weather station data. Plots actuals and
      climatology, produces wind and initial spread index roses for specific stations and time periods, and calculates
      long-term fire analyst and risk landscape polygons based on climatology.
    </Typography>
  ),
  icon: <AirOutlinedIcon color="primary" fontSize="large" />,
  isBeta: false,
  managedBy: WX_DATA_VIEWER_MANAGING_TEAM,
  isExternal: true
}

export const externalToolInfos = [wxDataViewerInfo]
