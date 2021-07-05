import { TextField } from '@material-ui/core'
import { DateTime } from 'luxon'
import React from 'react'

interface DatePickerProps {
  testId?: string
  date: string
  onChange: (d: string) => void
}

const DatePicker = (props: DatePickerProps) => {
  return (
    <TextField
      data-testid="date-of-interest-picker"
      label="Date of Interest (PST-08:00)"
      type="date"
      value={props.date.slice(0, 10)} // 'YYYY-MM-DD'
      variant="outlined"
      onChange={e => {
        const value = e.currentTarget.value

        if (value) {
          props.onChange(value)
        }
      }}
    />
  )
}

export default React.memo(DatePicker)
