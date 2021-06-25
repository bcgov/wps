import React from 'react'
import { makeStyles } from '@material-ui/core/styles'
import { FormControl, InputLabel, Select } from '@material-ui/core'
import { MenuItem } from '@material-ui/core'

enum AccuracyWeatherVariable {
  'Relative Humidity' = 1,
  'Temperature'
}

const useStyles = makeStyles({
  variableDropdown: {
    minWidth: 250,
    margin: '8px',
    marginLeft: '20px'
  },
  select: {
    color: 'white'
  }
})

const AccuracyVariablePicker = () => {
  const classes = useStyles()

  const [selectedAccuracyWxVariable, setSelectedAccuracyWxVariable] = React.useState(0)

  const handleChange = (event: React.ChangeEvent<{ value: unknown }>) => {
    setSelectedAccuracyWxVariable(event.target.value as AccuracyWeatherVariable)
  }

  return (
    <div>
      <FormControl className={classes.variableDropdown}>
        <InputLabel id="variable-dropdown-label" className={classes.select}>
          View accuracy map for
        </InputLabel>
        <Select
          labelId="variable-dropdown-label"
          id="accuracy-variable-dropdown"
          value={selectedAccuracyWxVariable}
          onChange={handleChange}
          className={classes.select}
        >
          <MenuItem value={AccuracyWeatherVariable['Relative Humidity']}>
            Relative Humidity
          </MenuItem>
          <MenuItem value={AccuracyWeatherVariable['Temperature']}>Temperature</MenuItem>
        </Select>
      </FormControl>
    </div>
  )
}

export default React.memo(AccuracyVariablePicker)
