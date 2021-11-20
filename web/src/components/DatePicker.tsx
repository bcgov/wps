import React from 'react'
import LuxonUtils from '@date-io/luxon'
import { KeyboardDatePicker, MuiPickersUtilsProvider } from '@material-ui/pickers'

interface DatePickerProps {
  testId?: string
  date: string
  updateDate: (d: string) => void
}

const DatePicker = (props: DatePickerProps) => {
  return (
    <MuiPickersUtilsProvider utils={LuxonUtils}>
      <KeyboardDatePicker
        label="Date of Interest (PST-08:00)"
        value={props.date}
        format="yyyy/MM/dd"
        allowKeyboardControl={true}
        InputAdornmentProps={{ position: 'start' }}
        onAccept={d => {
          if (d) {
            const newDate = d.setZone('UTC-7').toISO().slice(0, 10)
            props.updateDate(newDate)
            console.log('accept', newDate)
          }
        }}
        onKeyDown={event => {
          if (event.key === 'Enter') {
            const newDate = event.currentTarget
              //Gets the input component that holds the date value
              .getElementsByTagName('input')[0]
              .value.toString()
              //Replaces the '/' in the date with '-' otherwise the formatting is incompatible
              .replaceAll('/', '-')
            event.preventDefault()
            props.updateDate(newDate)
          }
        }}
        onBlur={event => {
          const newDate = event.currentTarget.value
            .toString()
            //Replaces the '/' in the date with '-' otherwise the formatting is incompatible
            .replaceAll('/', '-')
          event.preventDefault()
          props.updateDate(newDate)
        }}
        onChange={e => {
          /*This is a required attribute we don't use because 
          it makes editting the date with a keyboard impossible*/
        }}
      ></KeyboardDatePicker>
    </MuiPickersUtilsProvider>
  )
}
export default React.memo(DatePicker)
