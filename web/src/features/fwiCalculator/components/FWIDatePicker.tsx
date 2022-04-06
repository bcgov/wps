import React, { useState } from 'react'
import { TextField, IconButton, InputAdornment } from '@mui/material'
import FWIDateRange from 'features/fwiCalculator/components/FWIDateRange'
import { DateRange } from '@mui/icons-material'
import { DateTime } from 'luxon'
import { PST_UTC_OFFSET } from 'utils/constants'
import DatePicker from 'components/DatePicker'

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
  const displayFormat = 'dd/MM/yyyy'

  const updateStartDateWrapper = (startDateString: string) => {
    const newDate = DateTime.fromISO(startDateString)
      .startOf('day')
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
      {isBasic ? (
        <DatePicker
          label={'Date of Interest (PST-08:00)'}
          date={startDate.toISOString()}
          updateDate={updateStartDateWrapper}
        />
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
            value={`${DateTime.fromJSDate(startDate)
              .toFormat(displayFormat)
              .trim()} - ${DateTime.fromJSDate(endDate).toFormat(displayFormat).trim()}
                      `}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <IconButton
                    aria-label="toggle password visibility"
                    edge="end"
                    size="large"
                  >
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
