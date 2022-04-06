import {
  createTheme,
  Dialog,
  IconButton,
  InputAdornment,
  TextField,
  ThemeProvider,
  Theme,
  StyledEngineProvider,
  adaptV4Theme
} from '@mui/material'
import * as materialIcons from '@mui/icons-material'
import DateRangePickerWrapper from 'components/dateRangePicker/DateRangePickerWrapper'
import { DateRange } from 'components/dateRangePicker/types'
import { PrepDateRange } from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import { isUndefined } from 'lodash'
import { DateTime } from 'luxon'
import React, { useState } from 'react'

declare module '@mui/styles/defaultTheme' {
  // eslint-disable-next-line @typescript-eslint/no-empty-interface
  interface DefaultTheme extends Theme {}
}

export interface PrepDateRangeSelectorProps {
  dateRange?: PrepDateRange
  setDateRange: (newDateRange: DateRange) => void
}

export const dateRangePickerTheme = createTheme(
  adaptV4Theme({
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
)

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
      <StyledEngineProvider injectFirst>
        <ThemeProvider theme={dateRangePickerTheme}>
          <TextField
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
