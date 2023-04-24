import React, { useState } from 'react'
import makeStyles from '@mui/styles/makeStyles'
import { Grid, FormControl } from '@mui/material'
import {
  ForecastActionChoices,
  ForecastActionChoice,
  ModelOptions,
  ForecastActionType,
  ModelType,
  DEFAULT_MODEL_TYPE
} from 'api/moreCast2API'
import MoreCase2DateRangePicker from 'features/moreCast2/components/MoreCast2DateRangePicker'
import ForecastActionDropdown from 'features/moreCast2/components/ForecastActionDropdown'
import WeatherModelDropdown from 'features/moreCast2/components/WeatherModelDropdown'
import { DateRange } from 'components/dateRangePicker/types'

export interface MoreCast2ActionBarProps {
  children: React.ReactNode
  fromTo: DateRange
  setFromTo: React.Dispatch<React.SetStateAction<DateRange>>
  modelType: ModelType
  setModelType: React.Dispatch<React.SetStateAction<ModelType>>
  forecastAction: ForecastActionType
  setForecastAction: React.Dispatch<React.SetStateAction<ForecastActionType>>
}

const useStyles = makeStyles(theme => ({
  content: {
    display: 'flex',
    flexGrow: 1,
    maxHeight: 'calc(100vh - 71.5px)',
    borderTop: '1px solid black',
    overflow: 'hidden'
  },
  formControl: {
    minWidth: 280,
    margin: theme.spacing(1)
  },
  observations: {
    display: 'flex',
    flexDirection: 'column',
    flexGrow: 1,
    overflowX: 'auto'
  },
  root: {
    display: 'flex',
    flexDirection: 'column',
    minHeight: '100vh',
    overflow: 'hidden'
  },
  sidePanel: {
    borderRight: '1px solid black',
    display: 'flex',
    minWidth: '375px',
    overflowX: 'hidden',
    overflowY: 'auto',
    width: '375px'
  },
  actionButtonContainer: {
    marginTop: 15
  }
}))

const DEFAULT_MODEL_TYPE_KEY = 'defaultModelType'

const MoreCast2ActionBar = ({
  children,
  fromTo,
  setFromTo,
  forecastAction,
  setForecastAction
}: MoreCast2ActionBarProps) => {
  const classes = useStyles()
  console.log(JSON.stringify(fromTo))

  const [modelType, setModelType] = useState<ModelType>(
    (localStorage.getItem(DEFAULT_MODEL_TYPE_KEY) as ModelType) || DEFAULT_MODEL_TYPE
  )

  return (
    <Grid container spacing={1}>
      <Grid item xs={3}>
        <FormControl className={classes.formControl}>
          <ForecastActionDropdown
            forecastActionOptions={ForecastActionChoices}
            selectedForecastAction={forecastAction}
            setForecastAction={setForecastAction}
          />
        </FormControl>
      </Grid>
      {
        // Only show the weather model dropdown when creating new forecasts
        forecastAction === ForecastActionChoice.CREATE && (
          <Grid item xs={3}>
            <FormControl className={classes.formControl}>
              <WeatherModelDropdown
                weatherModelOptions={ModelOptions}
                selectedModelType={modelType}
                setSelectedModelType={setModelType}
              />
            </FormControl>
          </Grid>
        )
      }
      <Grid item xs={3}>
        <MoreCase2DateRangePicker dateRange={fromTo} setDateRange={setFromTo} />
      </Grid>
      <Grid item>{children}</Grid>
    </Grid>
  )
}

export default React.memo(MoreCast2ActionBar)
