import { SpotRequest, SpotRequestStatusColorMap } from '@/features/smurfi/interfaces'
import { Box, Button, Typography } from '@mui/material'
import { DataGridPro, GridColDef } from '@mui/x-data-grid-pro'
import { SpotRequestStatus } from '@wps/api/SMURFIAPI'
import { SMURFI_DASHBOARD_ROUTE, SMURFI_FORECASTS_ROUTE } from '@wps/utils/constants'
import { DateTime } from 'luxon'
import { useNavigate } from 'react-router-dom'

export interface SpotRequestsTableProps {
  rows: SpotRequest[]
}

const SpotRequestsTable = ({ rows }: SpotRequestsTableProps) => {
  const navigate = useNavigate()
  const columns: GridColDef<(typeof rows)[number]>[] = [
    { field: 'id', headerName: 'ID', width: 90 },
    { field: 'fireNumber', headerName: 'Fire Number', width: 110 },
    {
      field: 'fireCentre',
      headerName: 'Fire Centre',
      width: 150
    },
    {
      field: 'forecastStartDate',
      headerName: 'Start Date',
      width: 150,
      renderCell: params => {
        const dt = DateTime.fromISO(params.value)
        if (dt.isValid) {
          return dt.toISODate()
        }
      }
    },
    {
      field: 'forecastEndDate',
      headerName: 'End Date',
      width: 150,
      renderCell: params => {
        const dt = DateTime.fromISO(params.value)
        if (dt.isValid) {
          return dt.toISODate()
        }
      }
    },
    {
      field: 'status',
      headerName: 'Status',
      width: 100,
      renderCell: params => (
        <Box sx={{ display: 'flex', alignItems: 'center', width: '100%', height: '100%' }}>
          <Box
            sx={{
              backgroundColor: SpotRequestStatusColorMap[params.value as SpotRequestStatus].bgColor,
              borderRadius: '4px',
              alignItems: 'center',
              justifyContent: 'center',
              display: 'flex',
              flexGrow: 1,
              height: '70%',
              width: '100%',
              borderWidth: 1,
              borderStyle: 'solid',
              borderColor: SpotRequestStatusColorMap[params.value as SpotRequestStatus].borderColor
            }}
          >
            <Typography
              variant="body2"
              sx={{ color: SpotRequestStatusColorMap[params.value as SpotRequestStatus].color }}
            >
              {params.value}
            </Typography>
          </Box>
        </Box>
      )
    },
    {
      field: 'requestAction',
      headerName: 'View Request',
      width: 160,
      renderCell: params => (
        <Button variant="text" onClick={() => navigate(`${SMURFI_DASHBOARD_ROUTE}/${params.row.id}`)}>
          View Request
        </Button>
      )
    },
    {
      field: 'forecastAction',
      headerName: 'View Forecasts',
      width: 160,
      renderCell: params => (
        <Button variant="text" onClick={() => navigate(`${SMURFI_FORECASTS_ROUTE}/${params.row.id}`)}>
          View Forecasts
        </Button>
      )
    }
  ]

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column' }}>
      <DataGridPro columns={columns} rows={rows}></DataGridPro>
    </Box>
  )
}

export default SpotRequestsTable
