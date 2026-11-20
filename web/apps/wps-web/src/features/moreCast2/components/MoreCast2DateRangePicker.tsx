import { createTheme, ThemeProvider } from '@mui/material'
import DateRangeSelector from '@wps/ui/DateRangeSelector'
import type { DateRange } from '@wps/ui/dateRangePicker/types'
import { DateTime } from 'luxon'
import React from 'react'

export interface MoreCase2DateRangePickerProps {
  dateRange?: DateRange
  setDateRange: (newDateRange: DateRange) => void
}

export const dateRangePickerTheme = createTheme({
  components: {
    MuiOutlinedInput: {
      styleOverrides: {
        input: {
          '&.Mui-disabled': {
            color: 'rgba(0, 0, 0, 0.6);',
            WebkitTextFillColor: 'rgba(0, 0, 0, 0.6);'
          }
        }
      }
    },
    MuiFormLabel: {
      styleOverrides: {
        root: {
          '&.Mui-disabled': {
            color: 'rgba(0, 0, 0, 0.6);'
          }
        }
      }
    },
    MuiSvgIcon: {
      styleOverrides: {
        root: {
          fill: 'rgba(0, 0, 0, 0.6);'
        }
      }
    }
  }
})

const MoreCase2DateRangePicker = ({ dateRange, setDateRange }: MoreCase2DateRangePickerProps) => {
  return (
    <ThemeProvider theme={dateRangePickerTheme}>
      <DateRangeSelector
        dateRange={dateRange}
        minDate={DateTime.now().toJSDate()}
        maxDate={DateTime.now().plus({ days: 10 }).toJSDate()}
        maxDayOffset={11}
        dateDisplayFormat={'yyyy/MM/dd'}
        setDateRange={setDateRange}
        size="small"
        label={'Date Range'}
      />
    </ThemeProvider>
  )
}

export default React.memo(MoreCase2DateRangePicker)
