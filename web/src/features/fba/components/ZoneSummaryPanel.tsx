import React from 'react'
import { TextField } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import { isNull, isUndefined } from 'lodash'
import { FireZone, FireZoneThresholdFuelTypeArea, FuelType, HfiThreshold, HfiThresholdFuelTypeArea } from 'api/fbaAPI'

const useStyles = makeStyles({
  wrapper: {
    minWidth: 300
  },
  zoneName: {
    fontSize: '2rem'
  },
  centreName: {
    fontSize: '1.2rem'
  }
})

interface Props {
  className?: string
  selectedFireZone: FireZone | undefined
  fuelTypeInfo: Record<number, FireZoneThresholdFuelTypeArea[]>
}

const ZoneSummaryPanel = (props: Props) => {
  const classes = useStyles()

  console.log(props.fuelTypeInfo)

  if (isUndefined(props.selectedFireZone)) {
    return <div></div>
  } else {
    return (
      <div className={props.className}>
        <div className={classes.wrapper}>
          <TextField className={classes.zoneName} value={props.selectedFireZone.mof_fire_zone_name} />
          <TextField className={classes.centreName} value={props.selectedFireZone.mof_fire_centre_name} />
        </div>
        <div className={classes.wrapper}>{/* <TextField value={fireZoneFuelTypesData} /> */}</div>
      </div>
    )
  }
}

export default React.memo(ZoneSummaryPanel)
