import React, { useState, useEffect } from 'react'
import {
  Box,
  Button,
  Dialog,
  DialogContent,
  DialogTitle,
  Grid,
  IconButton,
  TextField,
  Autocomplete
} from '@mui/material'
import { useSelector, useDispatch } from 'react-redux'
import { selectSpotAdminRows } from '@/features/smurfi/slices/spotAdminSlice'
import { selectAuthentication } from '@/app/rootReducer'
import { fetchSubscriptions } from '@/features/smurfi/slices/subscriptionsSlice'
import { AppDispatch } from 'app/store'
import SpotRequestCard from '@/features/smurfi/components/SpotRequestCard'
import { DateRange } from '@wps/ui/dateRangePicker/types'
import DateRangeSelector from '@wps/ui/DateRangeSelector'
import CloseIcon from '@mui/icons-material/Close'
import SpotRequestForm from '@/features/smurfi/components/requestForm/SpotRequestForm'

const SpotRequest: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>()
  const spotAdminRows = useSelector(selectSpotAdminRows)
  const { isAuthenticated } = useSelector(selectAuthentication)
  const [searchTerm, setSearchTerm] = useState('')
  const [dateRange, setDateRange] = useState<DateRange | undefined>(undefined)
  const [fireCentreSearch, setFireCentreSearch] = useState('')
  const [forecasterSearch, setForecasterSearch] = useState('')
  const [statusSearch, setStatusSearch] = useState('')
  const [requestFormOpen, setRequestFormOpen] = useState(false)

  useEffect(() => {
    if (isAuthenticated) {
      dispatch(fetchSubscriptions())
    }
  }, [dispatch, isAuthenticated])

  const filteredSpots = spotAdminRows.filter(spot => {
    const matchesFireId = spot.fire_id.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesDate =
      !dateRange ||
      !dateRange.startDate ||
      !dateRange.endDate ||
      (spot.spot_end >= dateRange.startDate.getTime() && spot.spot_end <= dateRange.endDate.getTime())
    const matchesFireCentre = spot.fire_centre.toLowerCase().includes(fireCentreSearch.toLowerCase())
    const matchesForecaster = spot.forecaster.toLowerCase().includes(forecasterSearch.toLowerCase())
    const matchesStatus = statusSearch === '' || spot.status === statusSearch
    return matchesFireId && matchesDate && matchesFireCentre && matchesForecaster && matchesStatus
  })

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
      <Box sx={{ mt: 2, display: 'flex', gap: 2, alignItems: 'center' }}>
        <TextField
          label="Search by Fire ID"
          variant="outlined"
          value={searchTerm}
          onChange={e => setSearchTerm(e.target.value)}
          sx={{ flex: 1 }}
        />
        <DateRangeSelector
          dateRange={dateRange}
          setDateRange={setDateRange}
          dateDisplayFormat="yyyy/MM/dd"
          size="medium"
          label="Spot End Date Range"
        />
        <TextField
          label="Search by Fire Centre"
          variant="outlined"
          value={fireCentreSearch}
          onChange={e => setFireCentreSearch(e.target.value)}
          sx={{ flex: 1 }}
        />
        <TextField
          label="Search by Forecaster"
          variant="outlined"
          value={forecasterSearch}
          onChange={e => setForecasterSearch(e.target.value)}
          sx={{ flex: 1 }}
        />
        <Autocomplete
          sx={{ flex: 1 }}
          options={['New', 'Active', 'Inactive', 'Paused', 'Archived']}
          value={statusSearch || null}
          onChange={(event, newValue) => setStatusSearch(newValue || '')}
          renderInput={params => <TextField {...params} label="Search by Status" variant="outlined" />}
        />
      </Box>
      <Grid container spacing={2} sx={{ mt: 2 }}>
        {filteredSpots.map(spot => (
          <Grid size={{ xs: 6, sm: 4, md: 3 }} key={spot.id}>
            <SpotRequestCard spot={spot} isAuthenticated={isAuthenticated} />
          </Grid>
        ))}
      </Grid>
    </Box>
  )
}

export default SpotRequest
