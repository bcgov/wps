import React from 'react'
import makeStyles from '@mui/styles/makeStyles'
import { FormControl, InputLabel, Select, MenuItem } from '@mui/material'

export enum AccuracyWeatherVariableEnum {
  'Relative Humidity' = 1,
  'Temperature'
}

const useStyles = makeStyles({
  variableDropdown: {
    minWidth: 250,
    margin: '8px',
    marginLeft: '20px',
    '& label': {
      color: 'white !important'
    }
  },
  select: {
    color: 'white'
  }
})

interface Props {
  selectedWxVariable: AccuracyWeatherVariableEnum
  changeHandler: any //eslint-disable-line @typescript-eslint/no-explicit-any
}

const AccuracyVariablePicker = (props: Props) => {
  const classes = useStyles()

  return (
    <div>
      <FormControl variant="standard" className={classes.variableDropdown}>
        <InputLabel id="variable-dropdown-label" className={classes.select}>
          View accuracy map for
        </InputLabel>
        <Select
          labelId="variable-dropdown-label"
          id="accuracy-variable-dropdown"
          value={props.selectedWxVariable}
          className={classes.select}
          onChange={props.changeHandler}
        >
          <MenuItem value={AccuracyWeatherVariableEnum['Relative Humidity']}>Relative Humidity</MenuItem>
          <MenuItem value={AccuracyWeatherVariableEnum['Temperature']}>Temperature</MenuItem>
        </Select>
      </FormControl>
    </div>
  )
}

export default React.memo(AccuracyVariablePicker)
