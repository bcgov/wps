import React from 'react'
import { makeStyles } from '@material-ui/core/styles'
import TextField from '@material-ui/core/TextField'

const useStyles = makeStyles({
  datePicker: {
    display: 'block',
    width: 300,
    marginTop: 16,
    marginBottom: 20
  }
})

interface Props {
  timeOfInterest: string
  onChange: (d: string) => void
}

const TimeOfInterestPicker = (props: Props) => {
  const classes = useStyles()

  return (
    <TextField
      data-testid="time-of-interest-picker"
      className={classes.datePicker}
      label="Time of Interest (PST-08:00)"
      type="datetime-local"
      value={props.timeOfInterest.slice(0, 16)} // 'YYYY-MM-DDTHH:mm'
      helperText="Disclaimer: not all data may be available."
      InputLabelProps={{
        shrink: true
      }}
      inputProps={{
        step: 900 // 15 min
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

export default React.memo(TimeOfInterestPicker)
