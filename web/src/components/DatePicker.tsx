import React from 'react'
import LuxonUtils from '@date-io/luxon'
import { KeyboardDatePicker, MuiPickersUtilsProvider } from '@material-ui/pickers'
import { DateTime } from 'luxon'
import { pstFormatter } from 'utils/date'

interface DatePickerProps {
  testId?: string
  label?: string
  size?: 'small' | 'medium'
  date: string
  updateDate: (d: string) => void
}

const DatePicker = (props: DatePickerProps) => {
  return (
    <MuiPickersUtilsProvider utils={LuxonUtils}>
      <KeyboardDatePicker
        data-testid="date-of-interest-picker"
        label={props.label ? props.label : 'Date of Interest (PST-08:00)'}
        inputVariant="outlined"
        value={props.date}
        format="yyyy/MM/dd"
        size={props.size ? props.size : 'medium'}
        allowKeyboardControl={true}
        InputAdornmentProps={{ position: 'start' }}
        onAccept={d => {
          if (d) {
            const newDate = pstFormatter(d)
            props.updateDate(newDate)
          }
        }}
        onKeyDown={event => {
          if (event.key === 'Enter') {
            const newDateString = event.currentTarget
              //Gets the input component that holds the date value
              .getElementsByTagName('input')[0]
              .value.toString()

            const newDate = pstFormatter(DateTime.fromFormat(newDateString, 'yyyy/MM/dd'))
            event.preventDefault()
            props.updateDate(newDate)
          }
        }}
        onBlur={event => {
          const newDate = pstFormatter(
            DateTime.fromFormat(event.currentTarget.value.toString(), 'yyyy/MM/dd')
          )
          event.preventDefault()
          props.updateDate(newDate)
        }}
        onChange={() => {
          /*This is a required attribute we don't use because 
          it makes editting the date with a keyboard impossible*/
        }}
      ></KeyboardDatePicker>
    </MuiPickersUtilsProvider>
  )
}
export default React.memo(DatePicker)
