import {
  createTheme,
  Dialog,
  InputAdornment,
  TextField,
  ThemeProvider,
  StyledEngineProvider,
  Icon,
  Button
} from '@mui/material'
import { styled } from '@mui/material/styles'
import * as materialIcons from '@mui/icons-material'
import DateRangePickerWrapper from 'components/dateRangePicker/DateRangePickerWrapper'
import { DateRange } from 'components/dateRangePicker/types'
import { PrepDateRange } from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import { isUndefined } from 'lodash'
import { DateTime } from 'luxon'
import React, { useState } from 'react'
const PREFIX = 'PrepDateRangeSelector'

const DateRangePickerTextField = styled(TextField, {
  name: `${PREFIX}-dateRangePickerTextField`
})({
  color: 'white'
})

export interface PrepDateRangeSelectorProps {
  dateRange?: PrepDateRange
  setDateRange: (newDateRange: DateRange) => void
}

export const dateRangePickerTheme = createTheme({
  components: {
    MuiOutlinedInput: {
      styleOverrides: {
        input: {
          '&.Mui-disabled': {
            color: 'white',
            WebkitTextFillColor: 'white'
          }
        }
      }
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          color: 'white',
          minWidth: 300,
          '& .MuiOutlinedInput-root': {
            '&.Mui-disabled fieldset': {
              borderColor: 'white'
            }
          }
        }
      }
    },
    MuiFormLabel: {
      styleOverrides: {
        root: {
          '&.Mui-disabled': {
            color: 'white'
          }
        }
      }
    },
    MuiSvgIcon: {
      styleOverrides: {
        root: {
          fill: 'white'
        }
      }
    },
    MuiIconButton: {
      styleOverrides: {
        root: {
          paddingLeft: 0,
          paddingRight: 12
        }
      }
    }
  }
})

const PrepDateRangeSelector = ({ dateRange, setDateRange }: PrepDateRangeSelectorProps) => {
  const dateDisplayFormat = 'MMMM dd'
  const startDate = dateRange && dateRange.start_date ? DateTime.fromISO(dateRange.start_date).toJSDate() : undefined
  const endDate = dateRange && dateRange.end_date ? DateTime.fromISO(dateRange.end_date).toJSDate() : undefined

  const [dateRangePickerOpen, setDateRangePickerOpen] = useState<boolean>(false)
  const toggleDateRangePicker = () => setDateRangePickerOpen(!dateRangePickerOpen)

  return (
    <div>
      <StyledEngineProvider injectFirst>
        <ThemeProvider theme={dateRangePickerTheme}>
          <Button
            sx={{ textTransform: 'capitalize' }}
            data-testid="date-range-picker-button"
            onClick={() => setDateRangePickerOpen(!dateRangePickerOpen)}
          >
            <DateRangePickerTextField
              data-testid="date-range-picker-text-field"
              size="small"
              id="outlined-basic"
              variant="outlined"
              disabled={true}
              label={'Set prep period'}
              value={
                isUndefined(dateRange) || isUndefined(dateRange.start_date) || isUndefined(dateRange.end_date)
                  ? ''
                  : `${DateTime.fromISO(dateRange.start_date).toFormat(dateDisplayFormat).trim()} - ${DateTime.fromISO(
                      dateRange.end_date
                    )
                      .toFormat(dateDisplayFormat)
                      .trim()}
                            `
              }
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Icon>
                      <materialIcons.DateRange />
                    </Icon>
                  </InputAdornment>
                )
              }}
            />
          </Button>
        </ThemeProvider>
      </StyledEngineProvider>
      <Dialog open={dateRangePickerOpen} onClose={toggleDateRangePicker}>
        <DateRangePickerWrapper
          initialDateRange={{ startDate, endDate }}
          open={dateRangePickerOpen}
          toggle={toggleDateRangePicker}
          onChange={range => setDateRange(range)}
        />
      </Dialog>
    </div>
  )
}

export default React.memo(PrepDateRangeSelector)
