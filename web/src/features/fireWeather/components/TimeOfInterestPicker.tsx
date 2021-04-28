import React from 'react'
import TextField from '@material-ui/core/TextField'

interface Props {
  className?: string
  timeOfInterest: string
  onChange: (d: string) => void
}

const TimeOfInterestPicker = (props: Props) => {
  return (
    <TextField
      data-testid="time-of-interest-picker"
      className={props.className}
      label="Time of Interest (PST-08:00)"
      type="datetime-local"
      value={props.timeOfInterest.slice(0, 16)} // 'YYYY-MM-DDTHH:mm'
      variant="outlined"
      size="small"
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
