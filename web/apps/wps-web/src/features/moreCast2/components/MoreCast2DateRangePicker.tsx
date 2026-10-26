import { Box, createTheme, ThemeProvider } from '@mui/material'
import { styled } from '@mui/material/styles'
import DateRangeSelector from '@wps/ui/DateRangeSelector'
import type { DateRange } from '@wps/ui/dateRangePicker/types'
import { isActualForecastTestDate } from 'features/moreCast2/util'
import { DateTime } from 'luxon'
import React from 'react'

const PREFIX = 'MoreCast2DateRangePicker'

const classes = {
  container: `${PREFIX}-container`
}

const StyledBox = styled(Box)(({ theme }) => ({
  [`&.${classes.container}`]: {
    margin: theme.spacing(1)
  }
}))

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
  const today = DateTime.now()
  const testDate = DateTime.fromISO(new URLSearchParams(window.location.search).get('testActualForecastDate') ?? '')
  const minDate = isActualForecastTestDate(testDate) ? DateTime.min(today, testDate) : today

  return (
    <StyledBox className={classes.container}>
      <ThemeProvider theme={dateRangePickerTheme}>
        <DateRangeSelector
          dateRange={dateRange}
          minDate={minDate.toJSDate()}
          maxDate={DateTime.now().plus({ days: 10 }).toJSDate()}
          maxDayOffset={11}
          dateDisplayFormat={'yyyy/MM/dd'}
          setDateRange={setDateRange}
          size="medium"
          label={'Date Range'}
        />
      </ThemeProvider>
    </StyledBox>
  )
}

export default React.memo(MoreCase2DateRangePicker)
