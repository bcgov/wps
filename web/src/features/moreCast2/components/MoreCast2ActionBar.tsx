import React, { useState } from 'react'
import makeStyles from '@mui/styles/makeStyles'
import { Grid, FormControl } from '@mui/material'
import { ModelOptions, ModelType, DEFAULT_MODEL_TYPE } from 'api/moreCast2API'
import MoreCase2DateRangePicker from 'features/moreCast2/components/MoreCast2DateRangePicker'
import WeatherModelDropdown from 'features/moreCast2/components/WeatherModelDropdown'
import { DateRange } from 'components/dateRangePicker/types'

export interface MoreCast2ActionBarProps {
  children: React.ReactNode
  fromTo: DateRange
  setFromTo: React.Dispatch<React.SetStateAction<DateRange>>
  modelType: ModelType
  setModelType: React.Dispatch<React.SetStateAction<ModelType>>
}

const useStyles = makeStyles(theme => ({
  formControl: {
    minWidth: 280,
    margin: theme.spacing(1)
  }
}))

const DEFAULT_MODEL_TYPE_KEY = 'defaultModelType'

const MoreCast2ActionBar = ({ children, fromTo, setFromTo }: MoreCast2ActionBarProps) => {
  const classes = useStyles()

  const [modelType, setModelType] = useState<ModelType>(
    (localStorage.getItem(DEFAULT_MODEL_TYPE_KEY) as ModelType) || DEFAULT_MODEL_TYPE
  )

  return (
    <Grid container spacing={1}>
      <Grid item xs={3}>
        <FormControl className={classes.formControl}>
          <WeatherModelDropdown
            weatherModelOptions={ModelOptions}
            selectedModelType={modelType}
            setSelectedModelType={setModelType}
          />
        </FormControl>
      </Grid>
      <Grid item xs={3}>
        <MoreCase2DateRangePicker dateRange={fromTo} setDateRange={setFromTo} />
      </Grid>
      <Grid item>{children}</Grid>
    </Grid>
  )
}

export default React.memo(MoreCast2ActionBar)
