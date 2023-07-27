import { Button, Dialog, IconButton, InputAdornment, TextField } from '@mui/material'
import * as materialIcons from '@mui/icons-material'
import DateRangePickerWrapper from 'components/dateRangePicker/DateRangePickerWrapper'
import { DateRange } from 'components/dateRangePicker/types'
import { isUndefined } from 'lodash'
import { DateTime } from 'luxon'
import React, { useState } from 'react'

export interface DateRangeSelectorProps {
  dateRange?: DateRange
  minDate?: Date
  maxDate?: Date
  maxDayOffset?: number
  dateDisplayFormat: string
  size: 'small' | 'medium'
  label: string
  setDateRange: (newDateRange: DateRange) => void
}

const DateRangeSelector = ({ dateRange, dateDisplayFormat, size, label, setDateRange }: DateRangeSelectorProps) => {
  const startDate = dateRange && dateRange.startDate ? dateRange.startDate : undefined
  const endDate = dateRange && dateRange.endDate ? dateRange.endDate : undefined

  const [dateRangePickerOpen, setDateRangePickerOpen] = useState<boolean>(false)
  const toggleDateRangePicker = () => setDateRangePickerOpen(!dateRangePickerOpen)

  return (
    <React.Fragment>
      <Button
        sx={{ textTransform: 'capitalize' }}
        data-testid="date-range-picker-button"
        onClick={() => setDateRangePickerOpen(!dateRangePickerOpen)}
      >
        <TextField
          data-testid="date-range-picker-text-field"
          sx={{ minWidth: 280 }}
          size={size}
          variant="outlined"
          disabled={true}
          label={label}
          onClick={() => setDateRangePickerOpen(!dateRangePickerOpen)}
          value={
            isUndefined(dateRange) || isUndefined(dateRange.startDate) || isUndefined(dateRange.endDate)
              ? ''
              : `${DateTime.fromJSDate(dateRange.startDate).toFormat(dateDisplayFormat)} - ${DateTime.fromJSDate(
                  dateRange.endDate
                ).toFormat(dateDisplayFormat)}
                        `
          }
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <IconButton edge="end" size="large">
                  <materialIcons.DateRange />
                </IconButton>
              </InputAdornment>
            )
          }}
        />
      </Button>
      <Dialog open={dateRangePickerOpen} onClose={toggleDateRangePicker}>
        <DateRangePickerWrapper
          initialDateRange={{ startDate, endDate }}
          open={dateRangePickerOpen}
          toggle={toggleDateRangePicker}
          onChange={range => setDateRange(range)}
        />
      </Dialog>
    </React.Fragment>
  )
}

export default React.memo(DateRangeSelector)
