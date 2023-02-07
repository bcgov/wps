import React from 'react'
import { Grid, Typography } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import { isNull } from 'lodash'
import { FireZoneArea } from 'api/fbaAPI'
import CombustibleAreaViz from 'features/fba/components/viz/CombustibleAreaViz'

const useStyles = makeStyles({
  wrapper: {
    minWidth: 300
  }
})

interface Props {
  selectedZoneID: number | null
  fireZoneAreas: FireZoneArea[]
}

const ZoneSummaryPanel = (props: Props) => {
  const classes = useStyles()
  if (isNull(props.selectedZoneID)) {
    return <></>
  }

  return (
    <Grid container alignItems={'center'} direction={'column'} spacing={2} className={classes.wrapper}>
      <Grid item>
        <Typography>Zone ID: {props.selectedZoneID}</Typography>
      </Grid>
      <Grid item>
        <CombustibleAreaViz
          fireZoneAreas={props.fireZoneAreas.filter(area => area.mof_fire_zone_id == props.selectedZoneID)}
        />
      </Grid>
    </Grid>
  )
}

export default React.memo(ZoneSummaryPanel)
