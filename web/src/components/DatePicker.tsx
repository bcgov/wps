import React from 'react'
import LuxonUtils from '@date-io/luxon'
import { KeyboardDatePicker, MuiPickersUtilsProvider } from '@material-ui/pickers'
import { DateTime } from 'luxon'
import { PST_UTC_OFFSET } from 'utils/constants'

interface DatePickerProps {
  testId?: string
  date: string
  updateDate: (d: DateTime) => void
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
            const newDate = d.setZone('UTC' + PST_UTC_OFFSET).startOf('day')
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
            .setZone('UTC' + PST_UTC_OFFSET)
          console.log(newDate.toISO())

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
