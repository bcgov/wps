import {
  createTheme,
  Dialog,
  IconButton,
  InputAdornment,
  TextField,
  ThemeProvider
} from '@material-ui/core'
import * as materialIcons from '@material-ui/icons'
import DateRangePickerWrapper from 'components/dateRangePicker/DateRangePickerWrapper'
import { DateRange } from 'components/dateRangePicker/types'
import { PrepDateRange } from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import { isUndefined } from 'lodash'
import { DateTime } from 'luxon'
import React, { useState } from 'react'

export interface PrepDateRangeSelectorProps {
  dateRange?: PrepDateRange
  setDateRange: (newDateRange: DateRange) => void
}

export const dateRangePickerTheme = createTheme({
  overrides: {
    MuiOutlinedInput: {
      root: {
        '&.Mui-disabled': {
          color: 'white',
          borderColor: 'white',
          '& $notchedOutline': {
            borderColor: 'white'
          }
        }
      }
    },
    MuiFormLabel: {
      root: {
        '&.Mui-disabled': {
          color: 'white'
        }
      }
    },
    MuiSvgIcon: {
      root: {
        fill: 'white'
      }
    },
    MuiIconButton: {
      root: {
        paddingLeft: 0,
        paddingRight: 12
      }
    },
    MuiTextField: {
      root: {
        minWidth: 270
      }
    }
  }
})

const PrepDateRangeSelector = ({
  dateRange,
  setDateRange
}: PrepDateRangeSelectorProps) => {
  const dateDisplayFormat = 'MMMM dd'
  const startDate =
    dateRange && dateRange.start_date
      ? DateTime.fromISO(dateRange.start_date).toJSDate()
      : undefined
  const endDate =
    dateRange && dateRange.end_date
      ? DateTime.fromISO(dateRange.end_date).toJSDate()
      : undefined

  const [dateRangePickerOpen, setDateRangePickerOpen] = useState<boolean>(false)
  const toggleDateRangePicker = () => setDateRangePickerOpen(!dateRangePickerOpen)

  return (
    <React.Fragment>
      <ThemeProvider theme={dateRangePickerTheme}>
        <TextField
          data-testid="date-range-picker-text-field"
          size="small"
          id="outlined-basic"
          variant="outlined"
          disabled={true}
          label={'Set prep period'}
          onClick={() => setDateRangePickerOpen(!dateRangePickerOpen)}
          value={
            isUndefined(dateRange) ||
            isUndefined(dateRange.start_date) ||
            isUndefined(dateRange.end_date)
              ? ''
              : `${DateTime.fromISO(dateRange.start_date)
                  .toFormat(dateDisplayFormat)
                  .trim()} - ${DateTime.fromISO(dateRange.end_date)
                  .toFormat(dateDisplayFormat)
                  .trim()}
                      `
          }
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <IconButton edge="end">
                  <materialIcons.DateRange />
                </IconButton>
              </InputAdornment>
            )
          }}
        />
      </ThemeProvider>
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

export default React.memo(PrepDateRangeSelector)
