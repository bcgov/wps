import React from 'react'
import { AdapterLuxon } from '@mui/x-date-pickers/AdapterLuxon'
import { DatePicker, LocalizationProvider } from '@mui/x-date-pickers'
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
    <LocalizationProvider dateAdapter={AdapterLuxon}>
      <DatePicker
        label={props.label || 'Date of Interest (PST-08:00)'}
        format="yyyy/MM/dd"
        value={props.date}
        onChange={newValue => {
          if (!isNull(newValue)) {
            props.updateDate(newValue)
          }
        }}
      />
    </LocalizationProvider>
  )
}
export default React.memo(WPSDatePicker)
