import {
  createTheme,
  Dialog,
  IconButton,
  InputAdornment,
  TextField,
  ThemeProvider,
  Theme,
  StyledEngineProvider
} from '@mui/material'
import * as materialIcons from '@mui/icons-material'
import DateRangePickerWrapper from 'components/dateRangePicker/DateRangePickerWrapper'
import { DateRange } from 'components/dateRangePicker/types'
import { PrepDateRange } from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import { isUndefined } from 'lodash'
import { DateTime } from 'luxon'
import React, { useState } from 'react'
import { makeStyles } from '@mui/styles'

declare module '@mui/styles/defaultTheme' {
  // eslint-disable-next-line @typescript-eslint/no-empty-interface
  interface DefaultTheme extends Theme {}
}

export interface PrepDateRangeSelectorProps {
  dateRange?: PrepDateRange
  setDateRange: (newDateRange: DateRange) => void
}

const useStyles = makeStyles({
  autocomplete: {
    width: '100%',
    hasPopupIcon: 'true',
    hasClearIcon: 'true',
    color: 'white'
  },
  wrapper: {
    minWidth: 300
  },
  fireCentreTextField: {
    color: 'white',
    '& .MuiAutocomplete-clearIndicator': {
      color: 'white'
    },
    '& .MuiAutocomplete-popupIndicator': {
      color: 'white'
    },
    '& .MuiInputLabel-root': {
      color: 'white'
    },
    '& .MuiOutlinedInput-root': {
      '& fieldset': {
        borderColor: 'white'
      },
      '&:hover fieldset': {
        borderColor: 'white'
      },
      '&.Mui-focused fieldset': {
        borderColor: 'white'
      }
    }
  },
  textFieldInput: {
    color: 'white'
  }
})

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
  const classes = useStyles()
  const dateDisplayFormat = 'MMMM dd'
  const startDate = dateRange && dateRange.start_date ? DateTime.fromISO(dateRange.start_date).toJSDate() : undefined
  const endDate = dateRange && dateRange.end_date ? DateTime.fromISO(dateRange.end_date).toJSDate() : undefined

  const [dateRangePickerOpen, setDateRangePickerOpen] = useState<boolean>(false)
  const toggleDateRangePicker = () => setDateRangePickerOpen(!dateRangePickerOpen)

  return (
    <React.Fragment>
      <StyledEngineProvider injectFirst>
        <ThemeProvider theme={dateRangePickerTheme}>
          <TextField
            data-testid="date-range-picker-text-field"
            size="small"
            id="outlined-basic"
            variant="outlined"
            disabled={true}
            className={classes.textFieldInput}
            label={'Set prep period'}
            onClick={() => setDateRangePickerOpen(!dateRangePickerOpen)}
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
                  <IconButton edge="end" size="large">
                    <materialIcons.DateRange />
                  </IconButton>
                </InputAdornment>
              )
            }}
          />
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
    </React.Fragment>
  )
}

export default React.memo(PrepDateRangeSelector)
