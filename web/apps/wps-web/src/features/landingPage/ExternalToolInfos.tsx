import AreaChartOutlinedIcon from '@mui/icons-material/AreaChartOutlined'
import Typography from '@mui/material/Typography'
import { PUBLIC_TOOL_ICON_COLOUR, type ToolInfo } from 'features/landingPage/toolInfo'

export const WX_DATA_VIEWER_ROUTE = 'https://huggingface.co/spaces/ssidds/WX_data_viewer'
export const WX_DATA_VIEWER_MANAGING_TEAM = 'TBD'

export const wxDataViewerInfo: ToolInfo = {
  name: 'WX Data Viewer',
  route: WX_DATA_VIEWER_ROUTE,
  subheading: 'Weather station actuals, climatology, and wind analysis',
  description: (
    <Typography>
      A near real time and historical hourly visualizer of BCWS weather station data. Plots actuals and climatology,
      performs spread analysis, and calculates risk landscape polygons based on climatology.
    </Typography>
  ),
  icon: <AreaChartOutlinedIcon fontSize="large" htmlColor={PUBLIC_TOOL_ICON_COLOUR} />,
  isBeta: false,
  managedBy: WX_DATA_VIEWER_MANAGING_TEAM,
  isExternal: true
}

export const externalToolInfos = [wxDataViewerInfo]
