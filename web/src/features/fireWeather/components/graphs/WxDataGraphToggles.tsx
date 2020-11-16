import React from 'react'
import Typography from '@material-ui/core/Typography'
import { makeStyles } from '@material-ui/core/styles'
import FormGroup from '@material-ui/core/FormGroup'
import FormControlLabel from '@material-ui/core/FormControlLabel'
import Switch from '@material-ui/core/Switch'

import {
  ToggleValues,
  SetToggleValues
} from 'features/fireWeather/components/graphs/useGraphToggles'

const useStyles = makeStyles({
  switchControl: {
    marginLeft: -5
  },
  switchLabel: {
    marginLeft: 2
  },
  selectControl: {
    minWidth: 85,
    marginRight: 15
  }
})

interface Props {
  toggleValues: ToggleValues
  setToggleValues: SetToggleValues
  noObservations: boolean
  noModels: boolean
  noForecasts: boolean
  noBiasAdjModels: boolean
  noHighResModels: boolean
}

const WxDataToggles = ({
  toggleValues,
  setToggleValues,
  noObservations,
  noModels,
  noForecasts,
  noBiasAdjModels,
  noHighResModels
}: Props) => {
  const classes = useStyles()
  const handleSwitch = (e: React.ChangeEvent<{ name: string }>, checked: boolean) => {
    setToggleValues(e.target.name as keyof ToggleValues, checked)
    // Create a matomo event.
    if (window._mtm) {
      window._mtm.push({
        event: 'tempRHGraphToggle',
        toggle: {
          name: e.target.name,
          checked: checked ? 'show' : 'hide' // matomo doesn't play nice with booleans
        }
      })
    }
  }

  return (
    <FormGroup row>
      <FormControlLabel
        className={classes.switchControl}
        control={
          <Switch
            name="showObservations"
            data-testid="wx-graph-observation-toggle"
            checked={toggleValues.showObservations}
            disabled={noObservations}
            size="small"
            onChange={handleSwitch}
          />
        }
        label={
          <Typography className={classes.switchLabel} variant="body2">
            Observations
          </Typography>
        }
      />

      <FormControlLabel
        className={classes.switchControl}
        control={
          <Switch
            name="showForecasts"
            data-testid="wx-graph-forecast-toggle"
            checked={toggleValues.showForecasts}
            disabled={noForecasts}
            size="small"
            onChange={handleSwitch}
          />
        }
        label={
          <Typography className={classes.switchLabel} variant="body2">
            Noon Forecasts
          </Typography>
        }
      />

      <FormControlLabel
        className={classes.switchControl}
        control={
          <Switch
            name="showHighResModels"
            data-testid="wx-graph-high-res-model-toggle"
            checked={toggleValues.showHighResModels}
            disabled={noHighResModels}
            size="small"
            onChange={handleSwitch}
          />
        }
        label={
          <Typography className={classes.switchLabel} variant="body2">
            HRDPS
          </Typography>
        }
      />

      <FormControlLabel
        className={classes.switchControl}
        control={
          <Switch
            name="showModels"
            data-testid="wx-graph-global-model-toggle"
            checked={toggleValues.showModels}
            disabled={noModels}
            size="small"
            onChange={handleSwitch}
          />
        }
        label={
          <Typography className={classes.switchLabel} variant="body2">
            GDPS
          </Typography>
        }
      />

      <FormControlLabel
        className={classes.switchControl}
        control={
          <Switch
            name="showBiasAdjModels"
            data-testid="wx-graph-bias-toggle"
            checked={toggleValues.showBiasAdjModels}
            disabled={noBiasAdjModels}
            size="small"
            onChange={handleSwitch}
          />
        }
        label={
          <Typography className={classes.switchLabel} variant="body2">
            Bias Adjusted GDPS
          </Typography>
        }
      />
    </FormGroup>
  )
}

export default React.memo(WxDataToggles)
