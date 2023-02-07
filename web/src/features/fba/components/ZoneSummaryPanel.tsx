import React from 'react'
import { Grid, Paper, Typography } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import { isUndefined } from 'lodash'
import { FireZone, FireZoneThresholdFuelTypeArea } from 'api/fbaAPI'
import FuelTypesBreakdown from 'features/fba/components/FuelTypesBreakdown'

const useStyles = makeStyles({
  wrapper: {
    minWidth: 400
  },
  zoneName: {
    fontSize: '2rem',
    textAlign: 'center',
    variant: 'h2'
  },
  centreName: {
    fontSize: '1rem',
    textAlign: 'right',
    variant: 'h6'
  }
})

interface Props {
  className?: string
  selectedFireZone: FireZone | undefined
  fuelTypeInfo: Record<number, FireZoneThresholdFuelTypeArea[]>
}

const ZoneSummaryPanel = (props: Props) => {
  const classes = useStyles()

  if (isUndefined(props.selectedFireZone)) {
    return <div></div>
  } else {
    return (
      <div className={props.className}>
        <Grid item>
          <Paper>
            <div className={classes.wrapper}>
              <Typography className={classes.zoneName}>{props.selectedFireZone.mof_fire_zone_name}</Typography>
              <Typography className={classes.centreName}>{props.selectedFireZone.mof_fire_centre_name}</Typography>
            </div>
            <FuelTypesBreakdown selectedFireZone={props.selectedFireZone} fuelTypeInfo={props.fuelTypeInfo} />
          </Paper>
        </Grid>
      </div>
    )
  }
}

export default React.memo(ZoneSummaryPanel)
