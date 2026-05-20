import React, { useState } from 'react'
import { Box, Button, Dialog, DialogContent, DialogTitle, IconButton, TextField, Autocomplete } from '@mui/material'
import { useSelector } from 'react-redux'
import { selectSpotAdminRows } from '@/features/smurfi/slices/spotAdminSlice'
import { DateRange } from '@wps/ui/dateRangePicker/types'
import DateRangeSelector from '@wps/ui/DateRangeSelector'
import CloseIcon from '@mui/icons-material/Close'
import SpotRequestForm from '@/features/smurfi/components/requestForm/SpotRequestForm'
import SpotRequestsTable from '@/features/smurfi/components/requests/SpotRequestsTable'
import { selectSpotForecasts } from '@/features/smurfi/slices/smurfiSlice'
import { DateTime } from 'luxon'

const SpotRequests: React.FC = () => {
  const spotForecasts = useSelector(selectSpotForecasts)
  const [searchTerm, setSearchTerm] = useState('')
  const [dateRange, setDateRange] = useState<DateRange | undefined>(undefined)
  const [fireCentreSearch, setFireCentreSearch] = useState('')
  const [statusSearch, setStatusSearch] = useState('')
  const [requestFormOpen, setRequestFormOpen] = useState(false)

  const dateInRange = (endDate: string) => {
    if (!dateRange?.startDate || !dateRange?.endDate) {
      return true
    }
    const requestEnd = DateTime.fromISO(endDate)

    if (!requestEnd.isValid) {
      return true
    }

    const dateRangeStart = dateRange.startDate.getTime()
    const dateRangeEnd = dateRange.endDate.getTime()
    const requestEndMillis = requestEnd.toMillis()

    return requestEndMillis >= dateRangeStart && requestEndMillis <= dateRangeEnd
  }

  const filteredSpotRequests = spotForecasts.filter(spot => {
    const matchesFireId = spot.fireNumber.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesFireCentre = spot.fireCentre.toLowerCase().includes(fireCentreSearch.toLowerCase())
    const matchesStatus = statusSearch === '' || spot.status === statusSearch
    const matchesDate = dateInRange(spot.forecastEndDate)
    return matchesFireId && matchesDate && matchesFireCentre && matchesStatus
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
      <Box sx={{ pb: 2, mt: 2, display: 'flex', gap: 2, alignItems: 'center' }}>
        <TextField
          label="Search by Fire ID"
          variant="outlined"
          value={searchTerm}
          onChange={e => setSearchTerm(e.target.value)}
          sx={{ flex: 1 }}
        />
        <TextField
          label="Search by Fire Centre"
          variant="outlined"
          value={fireCentreSearch}
          onChange={e => setFireCentreSearch(e.target.value)}
          sx={{ flex: 1 }}
        />
        <DateRangeSelector
          dateRange={dateRange}
          setDateRange={setDateRange}
          dateDisplayFormat="yyyy/MM/dd"
          size="medium"
          label="Spot End Date Range"
        />
        <Autocomplete
          sx={{ flex: 1 }}
          options={['New', 'Active', 'Inactive', 'Paused', 'Archived']}
          value={statusSearch || null}
          onChange={(event, newValue) => setStatusSearch(newValue || '')}
          renderInput={params => <TextField {...params} label="Search by Status" variant="outlined" />}
        />
      </Box>
      <SpotRequestsTable rows={filteredSpotRequests} />
    </Box>
  )
}

export default SpotRequests
