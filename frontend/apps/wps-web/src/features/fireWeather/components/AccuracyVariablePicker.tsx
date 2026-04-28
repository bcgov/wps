import React from 'react'
import { styled } from '@mui/material/styles'
import { FormControl, InputLabel, Select, MenuItem } from '@mui/material'

const PREFIX = 'AccuracyVariablePicker'

const classes = {
  variableDropdown: `${PREFIX}-variableDropdown`,
  select: `${PREFIX}-select`
}

const Root = styled('div')({
  [`& .${classes.variableDropdown}`]: {
    minWidth: 250,
    margin: '8px',
    marginLeft: '20px',
    '& label': {
      color: 'white !important'
    }
  },
  [`& .${classes.select}`]: {
    color: 'white'
  }
})

export enum AccuracyWeatherVariableEnum {
  'Relative Humidity' = 1,
  'Temperature'
}

interface Props {
  selectedWxVariable: AccuracyWeatherVariableEnum
  changeHandler: any //eslint-disable-line @typescript-eslint/no-explicit-any
}

const AccuracyVariablePicker = (props: Props) => {
  return (
    <Root>
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
    </Root>
  )
}

export default React.memo(AccuracyVariablePicker)
