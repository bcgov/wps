import { TextField } from '@material-ui/core'
import React from 'react'

interface DatePickerProps {
  testId?: string
  date: string
  onChange: (d: string) => void
  updateDate: () => void
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
      onSelect={props.updateDate}
      onKeyDown={event => {
        if (event.key === 'Enter') {
          event.preventDefault()
          props.updateDate()
        }
      }}
    />
  )
}

export default React.memo(DatePicker)
