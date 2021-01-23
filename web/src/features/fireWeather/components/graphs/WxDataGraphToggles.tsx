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
  noObservations: boolean
  noModels: boolean
  noForecasts: boolean
  noBiasAdjModels: boolean
  noHighResModels: boolean
  noRegionalModels: boolean
}

const WxDataToggles = ({
  toggleValues,
  setToggleValues,
  noObservations,
  noModels,
  noForecasts,
  noBiasAdjModels,
  noHighResModels,
  noRegionalModels
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
            name="showHrdps"
            data-testid="wx-graph-high-res-model-toggle"
            checked={toggleValues.showHrdps}
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
            name="showRdps"
            data-testid="wx-graph-regional-model-toggle"
            checked={toggleValues.showRdps}
            disabled={noRegionalModels}
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
            data-testid="wx-graph-global-model-toggle"
            checked={toggleValues.showGdps}
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
            name="showBiasAdjGdps"
            data-testid="wx-graph-bias-toggle"
            checked={toggleValues.showBiasAdjGdps}
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
