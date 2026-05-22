import { selectFireCentres } from '@/app/rootReducer'
import useSpotPermissions from '@/features/smurfi/hooks/useSpotPermissions'
import { SpotRequestStatusColorMap } from '@/features/smurfi/interfaces'
import { Box, Button, Typography } from '@mui/material'
import { DataGridPro, GridColDef } from '@mui/x-data-grid-pro'
import { SpotRequestOutput, SpotRequestStatus } from '@wps/api/SMURFIAPI'
import { SMURFI_DASHBOARD_ROUTE } from '@wps/utils/constants'
import { DateTime } from 'luxon'
import { useSelector } from 'react-redux'
import { useNavigate } from 'react-router-dom'

export interface SpotRequestsTableProps {
  rows: SpotRequestOutput[]
}

const formatDate = (value: string | null | undefined) => {
  if (!value) {
    return null
  }
  const dateTime = DateTime.fromISO(value)
  return dateTime.isValid ? dateTime.toFormat('yyyy-MM-dd') : null
}

const formatDateTime = (value: string | null | undefined) => {
  if (!value) {
    return null
  }
  const dateTime = DateTime.fromISO(value)
  return dateTime.isValid ? dateTime.toFormat('yyyy-MM-dd HH:mm') : null
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
      width: 150,
      renderCell: params => {
        const dt = DateTime.fromISO(params.value)
        if (dt.isValid) {
          return dt.toISODate()
        }
      }
    },
    {
      field: 'end_at',
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
      field: 'latestForecastSubmittedAt',
      headerName: 'Last Forecast',
      width: 160,
      renderCell: params => formatDateTime(params.row.latest_forecast?.created_at) ?? '-'
    },
    {
      field: 'latestForecastEndAt',
      headerName: 'Forecast Through',
      width: 160,
      renderCell: params => formatDate(params.row.latest_forecast?.forecast_end_at) ?? '-'
    },
    {
      field: 'actions',
      headerName: 'Actions',
      width: isForecaster ? 260 : 180,
      sortable: false,
      renderCell: params => (
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', height: '100%' }}>
          <Button size="small" variant="text" onClick={() => navigate(`${SMURFI_DASHBOARD_ROUTE}/${params.row.id}`)}>
            Request
          </Button>
          <Button
            size="small"
            variant="text"
            onClick={() => navigate(`${SMURFI_DASHBOARD_ROUTE}/${params.row.id}/forecasts`)}
          >
            Forecasts
          </Button>
          {isForecaster && (
            <Button
              size="small"
              variant="outlined"
              onClick={() => navigate(`${SMURFI_DASHBOARD_ROUTE}/${params.row.id}/forecasts/new`)}
            >
              Submit
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
      ></DataGridPro>
    </Box>
  )
}

export default SpotRequestsTable
