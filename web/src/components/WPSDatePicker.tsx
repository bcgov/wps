import React, { useState } from 'react'
import { AdapterLuxon } from '@mui/x-date-pickers/AdapterLuxon'
import { DatePicker, LocalizationProvider } from '@mui/x-date-pickers'
import { DateTime } from 'luxon'
import { isNil, isNull } from 'lodash'

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
  const [selectedDate, setSelectedDate] = useState<DateTime | null>(props.date)

  const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter') {
      event.preventDefault()
      event.stopPropagation()
      if (selectedDate?.isValid) {
        props.updateDate(selectedDate)
      }
    }
  }

  let label = isNil(props.label) ? 'Date of Interest' : props.label

  return (
    <LocalizationProvider dateAdapter={AdapterLuxon}>
      <DatePicker
        label={label}
        format="yyyy/MM/dd"
        value={selectedDate}
        onAccept={(newValue: DateTime | null) => {
          if (!isNull(newValue) && newValue.isValid) {
            props.updateDate(newValue)
          }
        }}
        onChange={newValue => setSelectedDate(newValue)}
        slotProps={{
          textField: {
            onKeyDown: handleKeyDown
          }
        }}
      />
    </LocalizationProvider>
  )
}
export default React.memo(WPSDatePicker)