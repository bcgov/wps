import React from 'react'
import Autocomplete from '@material-ui/lab/Autocomplete'
import { TextField } from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'

const useStyles = makeStyles({
  root: {
    width: 300
  }
})

export const timeRangeOptions = ['10']

export const TimeRangeOptionsDropdown = () => {
  const classes = useStyles()
  return (
    <>
      <Autocomplete
        disabled
        data-testid="time-range-dropdown"
        defaultValue={timeRangeOptions[0]}
        options={timeRangeOptions}
        className={classes.root}
        renderInput={params => (
          <TextField
            {...params}
            label="Time Range (years)"
            variant="outlined"
            fullWidth
            size="small"
          />
        )}
      />
    </>
  )
}
