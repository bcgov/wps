import { selectFireCentres } from '@/app/rootReducer'
import useSpotPermissions from '@/features/smurfi/hooks/useSpotPermissions'
import SpotStatusControl from '@/features/smurfi/components/SpotStatusControl'
import { SpotRequestStatusColorMap } from '@/features/smurfi/interfaces'
import {
  formatRequestFrequency,
  formatSpotRequestDate,
  formatSpotRequestDateTimeWithDay,
  formatSpotRequestDateWithDay
} from '@/features/smurfi/utils/spotRequestFormatters'
import { Box, Button, Typography } from '@mui/material'
import { DataGridPro, GridColDef } from '@mui/x-data-grid-pro'
import { SpotRequestOutput, SpotRequestStatus } from '@wps/api/SMURFIAPI'
import { getSmurfiForecastsRoute, getSmurfiNewForecastRoute, getSmurfiRequestRoute } from '@wps/utils/constants'
import { useSelector } from 'react-redux'
import { useNavigate } from 'react-router-dom'

export interface SpotRequestsTableProps {
  rows: SpotRequestOutput[]
}

const compareNullableIsoDates = (firstDate: string | null | undefined, secondDate: string | null | undefined) => {
  if (!firstDate && !secondDate) {
    return 0
  }

  if (!firstDate) {
    return 1
  }

  if (!secondDate) {
    return -1
  }

  return Date.parse(firstDate) - Date.parse(secondDate)
}

const SpotRequestsTable = ({ rows }: SpotRequestsTableProps) => {
  const navigate = useNavigate()
  const { fireCentres } = useSelector(selectFireCentres)
  const { isForecaster } = useSpotPermissions(rows[0])
  const columns: GridColDef<(typeof rows)[number]>[] = [
    { field: 'id', headerName: 'ID', width: 90 },
    {
      field: 'fire_number',
      headerName: 'Fire Number',
      width: 160,
      renderCell: params => params.row.fire_number.join(', ')
    },
    {
      field: 'fire_centre',
      headerName: 'Fire Centre',
      width: 150,
      renderCell: params =>
        (fireCentres.find(fc => fc.id === params.value)?.name ?? String(params.value)).replace(/ Fire Centre$/, '')
    },
    {
      field: 'start_at',
      headerName: 'Start Date',
      width: 120,
      renderCell: params => formatSpotRequestDate(params.value) ?? '-'
    },
    {
      field: 'end_at',
      headerName: 'End Date',
      width: 120,
      renderCell: params => formatSpotRequestDate(params.value) ?? '-'
    },
    {
      field: 'status',
      headerName: 'Status',
      width: 150,
      renderCell: params => (
        <Box sx={{ display: 'flex', alignItems: 'center', width: '100%', height: '100%' }}>
          <SpotStatusControl spotRequest={params.row} fullWidth />
        </Box>
      ),
      sortComparator: (a, b) => {
        const order = [
          SpotRequestStatus.REQUESTED,
          SpotRequestStatus.STARTED,
          SpotRequestStatus.SUSPENDED,
          SpotRequestStatus.COMPLETE,
          SpotRequestStatus.ARCHIVED
        ]
        return order.indexOf(a) - order.indexOf(b)
      }
    },
    {
      field: 'request_frequency',
      headerName: 'Frequency',
      width: 120,
      renderCell: params => (
        <Box sx={{ display: 'flex', alignItems: 'center', width: '100%', height: '100%' }}>
          <Typography variant="body2" title={params.value?.join(', ')}>
            {formatRequestFrequency(params.value)}
          </Typography>
        </Box>
      )
    },
    {
      field: 'latestForecastSubmittedAt',
      headerName: 'Last Forecast',
      width: 190,
      valueGetter: (_value, row) => row.latest_forecast?.created_at ?? null,
      sortComparator: compareNullableIsoDates,
      renderCell: params => formatSpotRequestDateTimeWithDay(params.value) ?? '-'
    },
    {
      field: 'latestForecastEndAt',
      headerName: 'Forecast Through',
      width: 170,
      valueGetter: (_value, row) => row.latest_forecast?.forecast_end_at ?? null,
      sortComparator: compareNullableIsoDates,
      renderCell: params => formatSpotRequestDateWithDay(params.value) ?? '-'
    },
    {
      field: 'actions',
      headerName: 'Actions',
      width: isForecaster ? 260 : 180,
      sortable: false,
      renderCell: params => (
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', height: '100%' }}>
          <Button size="small" variant="text" onClick={() => navigate(getSmurfiRequestRoute(params.row.id))}>
            Request
          </Button>
          <Button size="small" variant="text" onClick={() => navigate(getSmurfiForecastsRoute(params.row.id))}>
            Forecasts
          </Button>
          {isForecaster && (
            <Button size="small" variant="outlined" onClick={() => navigate(getSmurfiNewForecastRoute(params.row.id))}>
              New Forecast
            </Button>
          )}
        </Box>
      )
    }
  ]

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column' }}>
      <DataGridPro
        columns={columns}
        rows={rows}
        disableColumnFilter
        disableColumnPinning
        disableColumnReorder
        disableColumnSelector
        disableRowSelectionOnClick
        initialState={{
          sorting: {
            sortModel: [
              { field: 'status', sort: 'asc' },
              { field: 'latestForecastSubmittedAt', sort: 'asc' }
            ]
          }
        }}
      ></DataGridPro>
    </Box>
  )
}

export default SpotRequestsTable
