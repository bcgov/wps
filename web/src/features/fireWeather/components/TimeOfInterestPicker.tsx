import React from 'react'
import { makeStyles } from '@material-ui/core/styles'
import TextField from '@material-ui/core/TextField'
import { formatDateInPST } from 'utils/date'

const useStyles = makeStyles({
  datePicker: {
    display: 'block',
    width: 300,
    marginTop: 16,
    marginBottom: 20
  }
})

interface Props {
  timeOfInterest: Date
  onChange: (d: Date) => void
}

const TimeOfInterestPicker = (props: Props) => {
  const classes = useStyles()

  return (
    <TextField
      data-testid="time-of-interest-picker"
      label="Time of Interest (PST-08:00)"
      type="datetime-local"
      value={formatDateInPST(props.timeOfInterest, 'YYYY-MM-DDTHH:mm')}
      helperText="Disclaimer: all data may not be available."
      className={classes.datePicker}
      InputLabelProps={{
        shrink: true
      }}
      inputProps={{
        step: 900 // 15 min
      }}
      onChange={e => {
        const value = e.currentTarget.value
        if (value) {
          props.onChange(new Date(value))
        }
      }}
    />
  )
}

export default React.memo(TimeOfInterestPicker)
