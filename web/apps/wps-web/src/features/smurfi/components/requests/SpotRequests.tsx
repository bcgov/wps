import React, { useEffect, useMemo, useState } from 'react'
import {
  Box,
  Button,
  Dialog,
  DialogContent,
  DialogTitle,
  IconButton,
  InputAdornment,
  TextField,
  Autocomplete,
  CircularProgress,
  Typography
} from '@mui/material'
import { useDispatch, useSelector } from 'react-redux'
import { selectFireCentres } from '@/app/rootReducer'
import { DateRangePicker } from '@mui/x-date-pickers-pro/DateRangePicker'
import { SingleInputDateRangeField } from '@mui/x-date-pickers-pro/SingleInputDateRangeField'
import CloseIcon from '@mui/icons-material/Close'
import SpotRequestForm from '@/features/smurfi/components/requestForm/SpotRequestForm'
import SpotRequestsTable from '@/features/smurfi/components/requests/SpotRequestsTable'
import { fetchSpotRequests, selectSmurfi } from '@/features/smurfi/slices/smurfiSlice'
import { DateTime } from 'luxon'
import { AppDispatch } from '@/app/store'
import { fetchFireCentres } from '@/commonSlices/fireCentresSlice'
import { SpotRequestStatus } from '@wps/api/SMURFIAPI'

const SpotRequests: React.FC = () => {
  const { spotRequests, spotRequestsError, spotRequestsLoading } = useSelector(selectSmurfi)
  const { fireCentres } = useSelector(selectFireCentres)
  const [searchTerm, setSearchTerm] = useState('')
  const [dateRange, setDateRange] = useState<[DateTime | null, DateTime | null]>([null, null])
  const [fireCentreSearch, setFireCentreSearch] = useState<number | null>(null)
  const [statusSearch, setStatusSearch] = useState<SpotRequestStatus | ''>('')
  const [requestFormOpen, setRequestFormOpen] = useState(false)

  const dispatch: AppDispatch = useDispatch()

  useEffect(() => {
    dispatch(fetchSpotRequests())
    dispatch(fetchFireCentres())
  }, [])

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
      const matchesDate = dateInRange(spot.end_at)
      return matchesFireId && matchesDate && matchesFireCentre && matchesStatus
    })
  }, [spotRequests, searchTerm, fireCentreSearch, statusSearch, dateRange])

  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'flex-start',
        mb: 2,
        flexDirection: 'column'
      }}
    >
      <Button variant="contained" onClick={() => setRequestFormOpen(true)} sx={{ maxWidth: '200px' }}>
        Request a Spot Forecast
      </Button>
      <Dialog
        open={requestFormOpen}
        onClose={() => setRequestFormOpen(false)}
        maxWidth="md"
        fullWidth
        slotProps={{
          paper: {
            sx: { maxHeight: '90vh' }
          }
        }}
      >
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          Request a Spot Forecast
          <IconButton aria-label="close" onClick={() => setRequestFormOpen(false)} size="small">
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent dividers>
          <SpotRequestForm onCancel={() => setRequestFormOpen(false)} onSubmit={() => setRequestFormOpen(false)} />
        </DialogContent>
      </Dialog>
      <Box sx={{ pb: 2, mt: 2, display: 'flex', gap: 2, alignItems: 'center' }}>
        <TextField
          label="Search by Fire ID"
          variant="outlined"
          value={searchTerm}
          onChange={e => setSearchTerm(e.target.value)}
          sx={{ flex: 1 }}
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
          sx={{ flex: 1 }}
          options={fireCentres}
          getOptionLabel={option => option.name}
          value={fireCentres.find(fc => fc.id === fireCentreSearch) ?? null}
          onChange={(_, newValue) => setFireCentreSearch(newValue?.id ?? null)}
          renderInput={params => <TextField {...params} label="Search by Fire Centre" variant="outlined" />}
        />
        <DateRangePicker
          value={dateRange}
          onChange={setDateRange}
          label="Spot End Date Range"
          slots={{ field: SingleInputDateRangeField }}
          slotProps={{ field: { clearable: true }, textField: { sx: { flex: 1 } } }}
        />
        <Autocomplete
          sx={{ flex: 1 }}
          options={[
            SpotRequestStatus.REQUESTED,
            SpotRequestStatus.STARTED,
            SpotRequestStatus.SUSPENDED,
            SpotRequestStatus.COMPLETE,
            SpotRequestStatus.ARCHIVED
          ]}
          value={statusSearch || null}
          onChange={(event, newValue) => setStatusSearch(newValue || '')}
          renderInput={params => <TextField {...params} label="Search by Status" variant="outlined" />}
        />
      </Box>
      {spotRequestsLoading && <CircularProgress aria-label="Loading…" />}
      {spotRequestsError && (
        <Typography variant="body1">
          An error occurred while retrieving the list of Spot Requests. Please try again.
        </Typography>
      )}
      {!spotRequestsLoading && !spotRequestsError && <SpotRequestsTable rows={filteredSpotRequests} />}
    </Box>
  )
}

export default SpotRequests
