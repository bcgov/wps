import React from 'react'
import { TextField } from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'

const useStyles = makeStyles({
  root: {
    marginTop: 15,
    width: 300
  }
})

export const TimeRangeTextfield = () => {
  const classes = useStyles()

  return (
    <div>
      <TextField
        id="time-range-textfield"
        className={classes.root}
        data-testid="time-range-textfield"
        disabled
        label="Time Range (years)"
        defaultValue="10"
        variant="outlined"
        size="small"
      />
    </div>
  )
}
