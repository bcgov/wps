import React from 'react'
import LuxonUtils from '@date-io/luxon'
import { KeyboardDatePicker, MuiPickersUtilsProvider } from '@material-ui/pickers'
import { DateTime } from 'luxon'

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
            const newDate = d.startOf('day').setZone('UTC-8').toISO()
            props.updateDate(newDate)
          }
        }}
        onKeyDown={event => {
          if (event.key === 'Enter') {
            const newDateString = event.currentTarget
              //Gets the input component that holds the date value
              .getElementsByTagName('input')[0]
              .value.toString()

            const newDate = DateTime.fromFormat(newDateString, 'yyyy/MM/dd')
              .startOf('day')
              .setZone('UTC-8')
              .toISO()
            event.preventDefault()
            props.updateDate(newDate)
          }
        }}
        onBlur={event => {
          const newDate = DateTime.fromFormat(
            event.currentTarget.value.toString(),
            'yyyy/MM/dd'
          )
            .startOf('day')
            .setZone('UTC-8')
            .toISO()
          event.preventDefault()
          props.updateDate(newDate)
        }}
        onChange={e => {
          /*This is a required attribute we don't use because 
          it makes editting the date with a keyboard impossible*/
          console.log(e)
        }}
      ></KeyboardDatePicker>
    </MuiPickersUtilsProvider>
  )
}
export default React.memo(DatePicker)
