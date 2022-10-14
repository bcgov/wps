import React from 'react'
import TextField from '@mui/material/TextField'
import AdapterDateFns from '@mui/lab/AdapterLuxon'
import LocalizationProvider from '@mui/lab/LocalizationProvider'
import DatePicker from '@mui/lab/DatePicker'
import { DateTime } from 'luxon'
import { isNull } from 'lodash'

interface WPSDatePickerProps {
  testId?: string
  label?: string
  size?: 'small' | 'medium'
  date: DateTime
  updateDate: (d: DateTime) => void
  minDate?: DateTime
  maxDate?: DateTime
}

const WPSDatePicker = (props: WPSDatePickerProps) => {
  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <DatePicker
        label="Date of Interest (PST-08:00)"
        inputFormat="yyyy/MM/dd"
        value={props.date}
        onChange={newValue => {
          if (!isNull(newValue)) {
            props.updateDate(newValue)
          }
        }}
        renderInput={params => <TextField {...params} />}
      />
    </LocalizationProvider>
  )
}
export default React.memo(WPSDatePicker)
