import React, { useState } from 'react'
import { Box, Button, Grid, TextField, Autocomplete } from '@mui/material'
import { useSelector } from 'react-redux'
import { selectSpotAdminRows } from '@/features/smurfi/slices/spotAdminSlice'
import SpotRequestCard from '@/features/smurfi/components/SpotRequestCard'
import DateRangeSelector from '@/components/DateRangeSelector'
import { DateRange } from '@/components/dateRangePicker/types'

const SpotRequest: React.FC = () => {
  const spotAdminRows = useSelector(selectSpotAdminRows)
  const [searchTerm, setSearchTerm] = useState('')
  const [dateRange, setDateRange] = useState<DateRange | undefined>(undefined)
  const [fireCentreSearch, setFireCentreSearch] = useState('')
  const [forecasterSearch, setForecasterSearch] = useState('')
  const [statusSearch, setStatusSearch] = useState('')

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
      <Button
        variant="contained"
        href="https://submit.digital.gov.bc.ca/app/form/submit?f=e5a6ec9b-ead7-4f5b-bdcb-88f53caae53d"
        target="_blank"
        rel="noopener noreferrer"
        sx={{ maxWidth: '200px' }}
      >
        Request a Spot Forecast
      </Button>
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
          <Grid item xs={6} sm={4} md={3} key={spot.id}>
            <SpotRequestCard spot={spot} />
          </Grid>
        ))}
      </Grid>
    </Box>
  )
}

export default SpotRequest
