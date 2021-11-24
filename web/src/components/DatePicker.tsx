import React from 'react'
import LuxonUtils from '@date-io/luxon'
import { KeyboardDatePicker, MuiPickersUtilsProvider } from '@material-ui/pickers'
import { DateTime } from 'luxon'

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
        allowKeyboardControl={true}
        InputAdornmentProps={{ position: 'start' }}
        onAccept={d => {
          if (d) {
            const newDate = d.startOf('day').setZone('UTC-8').toISO()
            props.onChange(newDate)
            props.updateDate()
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
            props.onChange(newDate)
            props.updateDate()
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
          props.onChange(newDate)
          props.updateDate()
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
