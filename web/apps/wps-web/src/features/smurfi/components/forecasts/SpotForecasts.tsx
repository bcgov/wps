import { AppDispatch } from '@/app/store'
import { selectFireCentres } from '@/app/rootReducer'
import { fetchSpotForecasts, selectSmurfi } from '@/features/smurfi/slices/smurfiSlice'
import { formatDateTime, TIMEZONE } from '@/features/smurfi/utils/spotForecastUtils'
import { DateTime } from 'luxon'
import useSpotPermissions from '@/features/smurfi/hooks/useSpotPermissions'
import { SpotRequestStatusColorMap } from '@/features/smurfi/interfaces'
import { Field } from '@/features/smurfi/components/forecasts/SpotForecastComponents'
import { formatRequestFrequency, formatSpotRequestDate } from '@/features/smurfi/utils/spotRequestFormatters'
import { Box, Button, CircularProgress, Divider, Paper, Typography } from '@mui/material'
import { DataGridPro, GridColDef } from '@mui/x-data-grid-pro'
import { SpotRequestStatus } from '@wps/api/SMURFIAPI'
import { getSmurfiEditForecastRoute, getSmurfiForecastRoute, getSmurfiNewForecastRoute } from '@wps/utils/constants'
import { useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { useNavigate, useParams } from 'react-router-dom'

const SpotForecasts = () => {
  const { id } = useParams<{ id: string }>()
  const dispatch = useDispatch<AppDispatch>()
  const navigate = useNavigate()
  const { spotRequests, spotForecastsByRequestId, spotForecastsLoading } = useSelector(selectSmurfi)
  const { fireCentres } = useSelector(selectFireCentres)

  const spotRequestId = Number(id)

  useEffect(() => {
    if (!spotForecastsByRequestId[spotRequestId]) {
      dispatch(fetchSpotForecasts(spotRequestId))
    }
  }, [dispatch, spotRequestId, spotForecastsByRequestId])

  const spotRequest = spotRequests.find(sr => sr.id === spotRequestId)
  const { isForecaster } = useSpotPermissions(spotRequest)

  if (spotForecastsLoading) {
    return <CircularProgress />
  }

  const fireNumber = spotRequest?.fire_number?.join(', ') ?? '—'
  const fireCentreName = spotRequest
    ? (fireCentres.find(fc => fc.id === spotRequest.fire_centre)?.name ?? String(spotRequest.fire_centre)).replace(
        / Fire Centre$/,
        ''
      )
    : '—'
  const status = spotRequest?.status
  const statusBadge = status ? (
    <Box
      sx={{
        backgroundColor: SpotRequestStatusColorMap[status as SpotRequestStatus].bgColor,
        borderRadius: '4px',
        display: 'inline-flex',
        alignItems: 'center',
        px: 1,
        py: 0.25,
        borderWidth: 1,
        borderStyle: 'solid',
        borderColor: SpotRequestStatusColorMap[status as SpotRequestStatus].borderColor
      }}
    >
      <Typography variant="body2" sx={{ color: SpotRequestStatusColorMap[status as SpotRequestStatus].color }}>
        {status}
      </Typography>
    </Box>
  ) : undefined

  const rows = spotForecastsByRequestId[spotRequestId] ?? []

  const columns: GridColDef<(typeof rows)[number]>[] = [
    { field: 'id', headerName: 'ID', width: 80 },
    {
      field: 'issued_at',
      headerName: 'Issued At',
      width: 230,
      renderCell: params => formatDateTime(params.value)
    },
    {
      field: 'expires_at',
      headerName: 'Expires At',
      width: 230,
      renderCell: params => {
        if (!params.value) return '—'
        const dt = DateTime.fromISO(params.value).setZone(TIMEZONE)
        return dt.isValid ? dt.toFormat('EEE, MMM d, yyyy') : params.value
      }
    },
    { field: 'forecaster_name', headerName: 'Forecaster', width: 180 },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 160,
      sortable: false,
      renderCell: params => (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, height: '100%' }}>
          <Button
            size="small"
            variant="text"
            onClick={() => navigate(getSmurfiForecastRoute(spotRequestId, params.row.id))}
          >
            View
          </Button>
          {params.api.getSortedRowIds()[0] === params.id && (
            <Button
              size="small"
              variant="text"
              onClick={() => navigate(getSmurfiEditForecastRoute(spotRequestId, params.row.id))}
            >
              Edit
            </Button>
          )}
        </Box>
      )
    }
  ]

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', flexGrow: 1 }}>
      <Paper variant="outlined" sx={{ p: 2.5, display: 'flex', flexDirection: 'column', mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="overline" color="text.secondary" sx={{ fontWeight: 600, letterSpacing: 1.5 }}>
            Request Info
          </Typography>
          {statusBadge}
        </Box>
        <Divider sx={{ mt: 0.5, mb: 2 }} />
        <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 2 }}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Field label="Start Date" value={formatSpotRequestDate(spotRequest?.start_at) ?? '—'} />
            <Field label="End Date" value={formatSpotRequestDate(spotRequest?.end_at) ?? '—'} />
          </Box>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Field label="Request Type" value={spotRequest?.request_type ?? '—'} />
            <Field label="Request Frequency" value={formatRequestFrequency(spotRequest?.request_frequency)} />
          </Box>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Field label="Fire Number" value={fireNumber} />
            <Field label="Fire Centre" value={fireCentreName} />
          </Box>
        </Box>
      </Paper>
      {isForecaster && (
        <Box sx={{ mb: 1 }}>
          <Button variant="outlined" size="small" onClick={() => navigate(getSmurfiNewForecastRoute(spotRequestId))}>
            New Forecast
          </Button>
        </Box>
      )}
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
            sortModel: [{ field: 'issued_at', sort: 'desc' }]
          }
        }}
        getCellClassName={params => {
          if (!params.row.expires_at) return ''
          const expiry = DateTime.fromISO(params.row.expires_at).setZone(TIMEZONE)
          return expiry.isValid && expiry < DateTime.now() ? 'expired-cell' : ''
        }}
        sx={{ '& .expired-cell': { opacity: 0.4 } }}
      />
    </Box>
  )
}

export default SpotForecasts
