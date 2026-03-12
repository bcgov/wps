import { createTheme, ThemeProvider, StyledEngineProvider, Box } from '@mui/material'
import { styled } from '@mui/material/styles'
import { DateRange } from 'components/dateRangePicker/types'
import { DateTime } from 'luxon'
import React from 'react'
import DateRangeSelector from 'components/DateRangeSelector'

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
  return (
    <StyledBox className={classes.container}>
      <StyledEngineProvider injectFirst>
        <ThemeProvider theme={dateRangePickerTheme}>
          <DateRangeSelector
            dateRange={dateRange}
            minDate={DateTime.now().toJSDate()}
            maxDate={DateTime.now().plus({ days: 10 }).toJSDate()}
            maxDayOffset={11}
            dateDisplayFormat={'yyyy/MM/dd'}
            setDateRange={setDateRange}
            size="medium"
            label={'Date Range'}
          />
        </ThemeProvider>
      </StyledEngineProvider>
    </StyledBox>
  )
}

export default React.memo(MoreCase2DateRangePicker)
