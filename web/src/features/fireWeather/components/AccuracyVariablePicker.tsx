import React from 'react'
import { makeStyles } from '@material-ui/core/styles'
import Autocomplete from '@material-ui/lab/Autocomplete'
import { TextField } from '@material-ui/core'

const useStyles = makeStyles({
  autocomplete: {
    minWidth: 250,
    margin: '8px'
  },
  textField: {
    color: 'white'
  }
})

const weatherVariables = ['Relative Humidity', 'Temperature']

const AccuracyVariablePicker = () => {
  const classes = useStyles()
  return (
    <Autocomplete
      id="forecast-accuracy-variable-dropdown"
      data-testid="forecast-accuracy-variable-dropdown"
      className={classes.autocomplete}
      options={weatherVariables}
      renderInput={params => (
        <TextField
          {...params}
          label="View accuracy map for"
          variant="outlined"
          size="small"
        />
      )}
    />
  )
}

export default React.memo(AccuracyVariablePicker)
