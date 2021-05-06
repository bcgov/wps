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
  root: {
    marginBottom: 5
  },
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
  hasObservations: boolean
  hasModels: boolean
  hasForecasts: boolean
  hasBiasAdjModels: boolean
  hasHighResModels: boolean
  hasRegionalModels: boolean
}

const WxDataToggles = ({
  toggleValues,
  setToggleValues,
  hasObservations,
  hasModels,
  hasForecasts,
  hasBiasAdjModels,
  hasHighResModels,
  hasRegionalModels
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
    <FormGroup className={classes.root} row>
      <FormControlLabel
        className={classes.switchControl}
        control={
          <Switch
            name="showObservations"
            data-testid="wx-graph-observation-toggle"
            checked={toggleValues.showObservations}
            disabled={!hasObservations}
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
            disabled={!hasForecasts}
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
            name="showHrdps"
            data-testid="wx-graph-hrdps-toggle"
            checked={toggleValues.showHrdps}
            disabled={!hasHighResModels}
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
            name="showRdps"
            data-testid="wx-graph-rdps-toggle"
            checked={toggleValues.showRdps}
            disabled={!hasRegionalModels}
            size="small"
            onChange={handleSwitch}
          />
        }
        label={
          <Typography className={classes.switchLabel} variant="body2">
            RDPS
          </Typography>
        }
      />

      <FormControlLabel
        className={classes.switchControl}
        control={
          <Switch
            name="showGdps"
            data-testid="wx-graph-gdps-toggle"
            checked={toggleValues.showGdps}
            disabled={!hasModels}
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
            name="showBiasAdjGdps"
            data-testid="wx-graph-bias-adjusted-gdps-toggle"
            checked={toggleValues.showBiasAdjGdps}
            disabled={!hasBiasAdjModels}
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
