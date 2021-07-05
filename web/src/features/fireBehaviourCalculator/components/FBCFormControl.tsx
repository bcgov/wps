import React, { useState } from 'react'
import { makeStyles } from '@material-ui/core/styles'

import { DateTime } from 'luxon'
import { FormControl, InputLabel, MenuItem, Select, TextField } from '@material-ui/core'
import { Button } from 'components'
import TimeOfInterestPicker from 'features/fireWeather/components/TimeOfInterestPicker'
import DatePicker from './DatePicker'

const useStyles = makeStyles(theme => ({
  formControl: {
    margin: theme.spacing(1),
    minWidth: 180
  },
  timeOfInterest: {
    marginRight: 16
  }
}))

interface FBCFormControlProps {
  testId?: string
}

const FBCFormControl = (props: FBCFormControlProps) => {
  const classes = useStyles()

  const [dateOfInterest, setDateOfInterest] = useState(DateTime.now().toISODate())

  return (
    <div>
      <FormControl className={classes.formControl}>
        <InputLabel id="fbc-date-input">Weather Station</InputLabel>
        <Select labelId="fbc-weather-date-select" id="demo-date-select" value={322}>
          <MenuItem value={10}>Ten</MenuItem>
          <MenuItem value={20}>Twenty</MenuItem>
          <MenuItem value={30}>Thirty</MenuItem>
        </Select>
      </FormControl>
      <FormControl className={classes.formControl}>
        <DatePicker date={dateOfInterest} onChange={setDateOfInterest} />
      </FormControl>
      <FormControl className={classes.formControl}>
        <InputLabel id="fbc-date-input">Input Fuel Type</InputLabel>
        <Select labelId="fbc-weather-date-select" id="demo-date-select" value={'C5'}>
          <MenuItem value={10}>C5</MenuItem>
          <MenuItem value={20}>C6</MenuItem>
          <MenuItem value={30}>C7</MenuItem>
        </Select>
      </FormControl>
      <FormControl className={classes.formControl}>
        <TextField id="standard-basic" label="Input Grass Cure %" />
      </FormControl>
      <FormControl className={classes.formControl}>
        <Button
          data-testid="get-wx-data-button"
          variant="contained"
          color="primary"
          spinnercolor="white"
        >
          Calculate
        </Button>
      </FormControl>
    </div>
  )
}

export default React.memo(FBCFormControl)
