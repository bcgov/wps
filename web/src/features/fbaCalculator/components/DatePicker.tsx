import { TextField } from '@material-ui/core'
import React from 'react'

interface DatePickerProps {
  testId?: string
  date: string
  onChange: (d: string) => void
  autoUpdateHandler: () => void
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
      onBlur={props.autoUpdateHandler}
      onKeyDown={event => {
        if (event.key === 'Enter') {
          event.preventDefault()
          props.autoUpdateHandler()
        }
      }}
    />
  )
}

export default React.memo(DatePicker)
