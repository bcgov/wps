import { Box } from '@mui/material'
import { DataGridPro, GridColDef } from '@mui/x-data-grid-pro'
import { DateTime } from 'luxon'

enum SpotForecastStatus {
  NEW = "new",
  ACTIVE = "active",
  INACTIVE = "inactive",
  PAUSED = "paused",
  ARCHIVED = "archived"
}

interface SpotAdminRow {
  id: number
  spotId: number
  fireId: string
  forecaster: string
  fireCentre: string
  status: SpotForecastStatus
  lastUpdated: DateTime | null
}

const SpotAdmin = () => {
  const columns: GridColDef<SpotAdminRow>[] = [
    {
      field: 'status',
      headerName: 'Status',
      width: 60
    },
    {
      field: 'spotId',
      headerName: 'Spot ID',
      width: 100
    },
    {
      field: 'fireId',
      headerName: 'Fire ID',
      width: 100
    },
    {
      field: 'forecaster',
      headerName: 'Forecaster',
      width: 145
    },
        {
      field: 'fireCentre',
      headerName: 'Fire Centre',
      width: 120
    },
    {
      field: "lastUpdated",
      headerName: "Last Updated",
      width: 120
    },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 120
    }
  ]

  const rows: SpotAdminRow[] = [
    {
      id: 1,
      spotId: 123,
      fireId: "V0800168",
      forecaster: "Matt MacDonald",
      fireCentre: "Coastal",
      status: SpotForecastStatus.NEW,
      lastUpdated: null,
    }
  ]

  return (
    <Box sx={{display: "flex", flexGrow: 1, pr: 3}}>
      <DataGridPro
        columns={columns}
        rows={rows}
        sx={{display: "flex", flexGrow: 1}}/>
    </Box>
  )
}

export default SpotAdmin
