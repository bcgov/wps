import {
  FormControl,
  IconButton,
  InputAdornment,
  makeStyles,
  TextField
} from '@material-ui/core'
import * as materialIcons from '@material-ui/icons'
import { selectHFICalculatorState } from 'app/rootReducer'
import { isUndefined } from 'lodash'
import { DateTime } from 'luxon'
import { DateRangePicker, DateRange } from 'materialui-daterange-picker'
import React, { useState } from 'react'
import { useSelector } from 'react-redux'

export interface PrepDateRangeSelectorProps {
  setDateRange: (newDateRange: DateRange) => void
}

const useStyles = makeStyles({
  dateRangeTextField: {
    marginLeft: '8px',
    '& .MuiOutlinedInput-input': {
      color: 'white'
    },
    '& .MuiIconButton-root': {
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
  dateRangePicker: {
    zIndex: 3200
  },
  minWidth210: {
    minWidth: 210
  }
})

const PrepDateRangeSelector = (props: PrepDateRangeSelectorProps) => {
  const classes = useStyles()
  const dateDisplayFormat = 'MMMM dd'
  const { result } = useSelector(selectHFICalculatorState)
  const dateRange = result?.date_range
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
      <TextField
        className={`${classes.dateRangeTextField} ${classes.minWidth210}`}
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
      <FormControl className={classes.dateRangePicker}>
        <DateRangePicker
          initialDateRange={{ startDate, endDate }}
          open={dateRangePickerOpen}
          toggle={toggleDateRangePicker}
          onChange={range => props.setDateRange(range)}
          definedRanges={[]}
        />
      </FormControl>
    </React.Fragment>
  )
}

export default React.memo(PrepDateRangeSelector)
