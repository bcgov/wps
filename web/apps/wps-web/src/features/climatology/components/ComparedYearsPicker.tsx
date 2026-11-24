import { Autocomplete, Box, Button, TextField } from '@mui/material'
import { yearsBefore } from '@/features/climatology/comparedYears'

export interface ComparedYearsPickerProps {
  // The selected year, which is not compared with itself.
  year: number
  // Every year there is to choose from, newest first.
  years: number[]
  compared: number[]
  // The most that can be compared.
  limit: number
  onChange: (years: number[]) => void
}

/** Choose the years drawn beside the selected one. */
const ComparedYearsPicker = ({ year, years, compared, limit, onChange }: ComparedYearsPickerProps) => {
  const full = compared.length >= limit
  const firstYear = years[years.length - 1]
  const lastYear = yearsBefore(year, 1, firstYear)
  const lastYears = yearsBefore(year, limit, firstYear)
  return (
    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, alignItems: 'center' }}>
      <Autocomplete
        multiple
        size="small"
        disableCloseOnSelect={limit > 1}
        sx={{ minWidth: 280 }}
        options={years.filter(option => option !== year)}
        value={compared}
        getOptionLabel={option => `${option}`}
        // With a limit of one, choosing another year takes its place.
        getOptionDisabled={option => limit > 1 && full && !compared.includes(option)}
        onChange={(_, chosen) => onChange(chosen.slice(-limit))}
        renderInput={params => (
          <TextField {...params} label={limit > 1 ? `Compare with (up to ${limit} years)` : 'Compare with'} />
        )}
      />
      <Button size="small" disabled={lastYear.length === 0} onClick={() => onChange(lastYear)}>
        Last year
      </Button>
      {limit > 1 && (
        <Button size="small" disabled={lastYears.length === 0} onClick={() => onChange(lastYears)}>
          Last {limit} years
        </Button>
      )}
    </Box>
  )
}

export default ComparedYearsPicker
