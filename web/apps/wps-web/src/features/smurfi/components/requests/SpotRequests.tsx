import { selectFireCentres } from '@/app/rootReducer'
import SpotForecasterFilter from '@/features/smurfi/components/SpotForecasterFilter'
import SpotRequestStatsButton from '@/features/smurfi/components/SpotRequestStatsButton'
import SpotRequestsTable from '@/features/smurfi/components/requests/SpotRequestsTable'
import { selectSmurfi } from '@/features/smurfi/slices/smurfiSlice'
import CloseIcon from '@mui/icons-material/Close'
import {
  Autocomplete,
  Box,
  Button,
  CircularProgress,
  IconButton,
  InputAdornment,
  TextField,
  Typography
} from '@mui/material'
import { LocalizationProvider } from '@mui/x-date-pickers-pro'
import { AdapterLuxon } from '@mui/x-date-pickers-pro/AdapterLuxon'
import { DateRangePicker } from '@mui/x-date-pickers-pro/DateRangePicker'
import { SingleInputDateRangeField } from '@mui/x-date-pickers-pro/SingleInputDateRangeField'
import { SpotRequestStatus } from '@wps/api/SMURFIAPI'
import { SMURFI_NEW_REQUEST_ROUTE } from '@wps/utils/constants'
import { DateTime } from 'luxon'
import React, { useMemo, useState } from 'react'
import { useSelector } from 'react-redux'
import { useNavigate } from 'react-router-dom'

const SpotRequests: React.FC = () => {
  const navigate = useNavigate()
  const { spotRequests, spotRequestsError, spotRequestsLoading } = useSelector(selectSmurfi)
  const { fireCentres } = useSelector(selectFireCentres)
  const [searchTerm, setSearchTerm] = useState('')
  const [dateRange, setDateRange] = useState<[DateTime | null, DateTime | null]>([null, null])
  const [fireCentreSearch, setFireCentreSearch] = useState<number | null>(null)
  const [statusSearch, setStatusSearch] = useState<SpotRequestStatus | ''>('')
  const [selectedForecaster, setSelectedForecaster] = useState<string | null>(null)

  const dateInRange = (endDate: string) => {
    const [start, end] = dateRange
    if (!start || !end) return true
    const requestEnd = DateTime.fromISO(endDate)
    if (!requestEnd.isValid) return true
    return requestEnd >= start && requestEnd <= end
  }

  const filteredSpotRequests = useMemo(() => {
    if (!spotRequests || spotRequests.length === 0) {
      return []
    }
    return spotRequests.filter(spot => {
      const matchesFireId = spot.fire_number.some(fn => fn.toLowerCase().includes(searchTerm.toLowerCase()))
      const matchesFireCentre = fireCentreSearch === null || spot.fire_centre === fireCentreSearch
      const matchesStatus = statusSearch === '' || spot.status === statusSearch
      const matchesForecaster =
        selectedForecaster === null || spot.latest_forecast?.forecaster_name === selectedForecaster
      const matchesDate = dateInRange(spot.end_at)
      return matchesFireId && matchesDate && matchesFireCentre && matchesStatus && matchesForecaster
    })
  }, [spotRequests, searchTerm, fireCentreSearch, statusSearch, selectedForecaster, dateRange])

  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'flex-start',
        mb: 2,
        flexDirection: 'column',
        minWidth: 0,
        width: '100%'
      }}
    >
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          gap: 2,
          flexWrap: 'wrap',
          minWidth: 0,
          width: '100%'
        }}
      >
        <Button
          variant="contained"
          onClick={() => navigate(SMURFI_NEW_REQUEST_ROUTE)}
          sx={{ flexShrink: 0, maxWidth: '100%' }}
        >
          Request a Spot Forecast
        </Button>
        <Box sx={{ flexShrink: 0 }}>
          <SpotRequestStatsButton spotRequests={filteredSpotRequests} />
        </Box>
      </Box>
      <Box
        sx={{
          pb: 2,
          mt: 2,
          display: 'grid',
          gap: 2,
          gridTemplateColumns: 'repeat(auto-fit, minmax(min(220px, 100%), 1fr))',
          minWidth: 0,
          width: '100%'
        }}
      >
        <TextField
          label="Search by Fire ID"
          variant="outlined"
          size="small"
          value={searchTerm}
          onChange={e => setSearchTerm(e.target.value)}
          slotProps={{
            input: {
              endAdornment: searchTerm && (
                <InputAdornment position="end">
                  <IconButton size="small" onClick={() => setSearchTerm('')}>
                    <CloseIcon fontSize="small" />
                  </IconButton>
                </InputAdornment>
              )
            }
          }}
        />
        <Autocomplete
          size="small"
          options={fireCentres}
          getOptionLabel={option => option.name}
          value={fireCentres.find(fc => fc.id === fireCentreSearch) ?? null}
          onChange={(_, newValue) => setFireCentreSearch(newValue?.id ?? null)}
          renderInput={params => (
            <TextField {...params} label="Search by Fire Centre" variant="outlined" size="small" />
          )}
        />
        <SpotForecasterFilter spotRequests={spotRequests} value={selectedForecaster} onChange={setSelectedForecaster} />
        <LocalizationProvider dateAdapter={AdapterLuxon}>
          <DateRangePicker
            value={dateRange}
            onChange={setDateRange}
            label="Spot End Date Range"
            slots={{ field: SingleInputDateRangeField }}
            slotProps={{ field: { clearable: true }, textField: { size: 'small' } }}
          />
        </LocalizationProvider>
        <Autocomplete
          size="small"
          options={[
            SpotRequestStatus.REQUESTED,
            SpotRequestStatus.STARTED,
            SpotRequestStatus.SUSPENDED,
            SpotRequestStatus.COMPLETE,
            SpotRequestStatus.ARCHIVED
          ]}
          value={statusSearch || null}
          onChange={(event, newValue) => setStatusSearch(newValue || '')}
          renderInput={params => <TextField {...params} label="Search by Status" variant="outlined" size="small" />}
        />
      </Box>
      {spotRequestsLoading && <CircularProgress aria-label="Loading…" />}
      {spotRequestsError && (
        <Typography variant="body1">
          An error occurred while retrieving the list of Spot Requests. Please try again.
        </Typography>
      )}
      {!spotRequestsLoading && !spotRequestsError && (
        <Box sx={{ minWidth: 0, overflowX: 'auto', width: '100%' }}>
          <SpotRequestsTable rows={filteredSpotRequests} />
        </Box>
      )}
    </Box>
  )
}

export default SpotRequests
