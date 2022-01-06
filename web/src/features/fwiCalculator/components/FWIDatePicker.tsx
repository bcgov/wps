import React, { useState } from 'react'
import { FormControl, TextField, IconButton, InputAdornment } from '@material-ui/core'
import FWIDateRange from 'features/fwiCalculator/components/FWIDateRange'
import { CalendarToday } from '@material-ui/icons'
import { DateTime } from 'luxon'
import { PST_UTC_OFFSET } from 'utils/constants'
import DatePicker from 'components/DatePicker'
import { pstFormatter } from 'utils/date'

export interface FWIDateRangeProps {
  isBasic: boolean
  startDate: Date
  endDate: Date
  updateStartDate: (newDate: Date) => void
  updateEndDate: (newDate: Date) => void
}

const FWIDatePicker = ({
  isBasic,
  startDate,
  updateStartDate,
  updateEndDate,
  endDate
}: FWIDateRangeProps) => {
  const [open, setOpen] = useState(false)
  const displayFormat = 'dd/MMM/yyyy'

  const updateStartDateWrapper = (startDateString: string) => {
    const newDate = DateTime.fromISO(startDateString)
      .setZone(`UTC${PST_UTC_OFFSET}`)
      .toJSDate()
    updateStartDate(newDate)
    /**
     * We update end to the same date
     * so that date range is always valid
     * if user switches to  multi day calculator
     */
    updateEndDate(newDate)
  }

  return (
    <React.Fragment>
      <FormControl variant="outlined">
        {isBasic ? (
          <DatePicker
            label={isBasic ? 'Date of Interest (PST-08:00)' : 'Start Date'}
            date={pstFormatter(
              DateTime.fromJSDate(startDate).setZone(`UTC${PST_UTC_OFFSET}`)
            )}
            updateDate={updateStartDateWrapper}
          />
        ) : (
          <React.Fragment>
            <TextField
              id="outlined-basic"
              variant="outlined"
              label={
                isBasic ? 'Date of Interest (PST-08:00)' : 'Dates of Interest (PST-08:00)'
              }
              onClick={() => setOpen(!open)}
              value={`${DateTime.fromJSDate(startDate)
                .setZone(`UTC${PST_UTC_OFFSET}`)
                .toFormat(displayFormat)
                .trim()} - ${DateTime.fromJSDate(endDate)
                .setZone(`UTC${PST_UTC_OFFSET}`)
                .toFormat(displayFormat)
                .trim()}
                      `}
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton aria-label="toggle password visibility" edge="end">
                      <CalendarToday />
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
      </FormControl>
    </React.Fragment>
  )
}
export default React.memo(FWIDatePicker)
