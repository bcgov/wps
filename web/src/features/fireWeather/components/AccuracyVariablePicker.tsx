import React from 'react'
import { makeStyles } from '@material-ui/core/styles'
import { FormControl, InputLabel, Select, MenuItem } from '@material-ui/core'

export enum AccuracyWeatherVariableEnum {
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
  },
  '& .MuiFormLabel-root.Mui-focused': {
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
      <FormControl className={classes.variableDropdown}>
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
          <MenuItem value={AccuracyWeatherVariableEnum['Relative Humidity']}>
            Relative Humidity
          </MenuItem>
          <MenuItem value={AccuracyWeatherVariableEnum['Temperature']}>
            Temperature
          </MenuItem>
        </Select>
      </FormControl>
    </div>
  )
}

export default React.memo(AccuracyVariablePicker)
