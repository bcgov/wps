import React, { useState } from 'react'
import { TextField, IconButton, InputAdornment } from '@mui/material'
import FWIDateRange from 'features/fwiCalculator/components/FWIDateRange'
import DateRange from '@mui/icons-material/DateRange'
import { DateTime } from 'luxon'
import WPSDatePicker from 'components/WPSDatePicker'

export interface FWIDateRangeProps {
  isBasic: boolean
  startDate: Date
  endDate: Date
  updateStartDate: (newDate: Date) => void
  updateEndDate: (newDate: Date) => void
}

const FWIDatePicker = ({ isBasic, startDate, updateStartDate, updateEndDate, endDate }: FWIDateRangeProps) => {
  const [open, setOpen] = useState(false)
  const displayFormat = 'dd/MM/yyyy'

  const updateStartDateWrapper = (newStartDate: DateTime) => {
    updateStartDate(newStartDate.toJSDate())
    /**
     * We update end to the same date
     * so that date range is always valid
     * if user switches to  multi day calculator
     */
    updateEndDate(newStartDate.toJSDate())
  }

  return (
    <React.Fragment>
      {isBasic ? (
        <WPSDatePicker date={DateTime.fromJSDate(startDate)} updateDate={updateStartDateWrapper} />
      ) : (
        <React.Fragment>
          <TextField
            fullWidth
            size="medium"
            id="outlined-basic"
            variant="outlined"
            disabled={true}
            label={'Dates of Interest (PST-08:00)'}
            onClick={() => setOpen(!open)}
            value={`${DateTime.fromJSDate(startDate).toFormat(displayFormat).trim()} - ${DateTime.fromJSDate(endDate)
              .toFormat(displayFormat)
              .trim()}
                      `}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <IconButton aria-label="toggle password visibility" edge="end">
                    <DateRange />
                  </IconButton>
                </InputAdornment>
              )
            }}
          />
          <FWIDateRange
            open={open}
            setOpen={setOpen}
            updateStartDate={updateStartDate}
            startDate={startDate}
            updateEndDate={updateEndDate}
            endDate={endDate}
          />
        </React.Fragment>
      )}
    </React.Fragment>
  )
}
export default React.memo(FWIDatePicker)
