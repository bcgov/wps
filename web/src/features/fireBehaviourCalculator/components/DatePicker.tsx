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
      type="datetime-local"
      value={props.date.slice(0, 16)} // 'YYYY-MM-DDTHH:mm'
      variant="outlined"
      size="small"
      InputLabelProps={{
        shrink: true
      }}
      onChange={e => {
        const value = e.currentTarget.value

        if (value) {
          props.onChange(`${value}:00-08:00`) // Append seconds and timezone (PST) at the end
        }
      }}
    />
  )
}

export default React.memo(DatePicker)
