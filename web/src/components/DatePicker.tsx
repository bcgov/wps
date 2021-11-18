import React from 'react'
import LuxonUtils from '@date-io/luxon'
import { KeyboardDatePicker, MuiPickersUtilsProvider } from '@material-ui/pickers'

interface DatePickerProps {
  testId?: string
  date: string
  onChange: (d: string) => void
  updateDate: () => void
}

const DatePicker = (props: DatePickerProps) => {
  return (
    <MuiPickersUtilsProvider utils={LuxonUtils}>
      <KeyboardDatePicker
        label="Date of Interest (PST-08:00)"
        value={props.date}
        format="yyyy/MM/dd"
        InputAdornmentProps={{ position: 'start' }}
        onChange={e => {
          const value = e.setZone('UTC-7').toISO()

          if (value) {
            props.onChange(value)
            props.updateDate()
          }
        }}
      ></KeyboardDatePicker>
    </MuiPickersUtilsProvider>
  )
}
export default React.memo(DatePicker)
