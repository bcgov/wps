import React from 'react'
import { styled } from '@mui/material/styles'
import CombustibleAreaViz from 'features/fba/components/viz/CombustibleAreaViz'
import { Grid, Typography } from '@mui/material'
import { isUndefined } from 'lodash'
import { ElevationInfoByThreshold, FireZone, FireZoneArea, FireZoneThresholdFuelTypeArea } from 'api/fbaAPI'
import ElevationInfoViz from 'features/fba/components/viz/ElevationInfoViz'
import FuelTypesBreakdown from 'features/fba/components/viz/FuelTypesBreakdown'

const PREFIX = 'ZoneSummaryPanel'

const classes = {
  wrapper: `${PREFIX}-wrapper`,
  header: `${PREFIX}-header`,
  zoneName: `${PREFIX}-zoneName`,
  centreName: `${PREFIX}-centreName`
}

const StyledGrid = styled(Grid)({
  [`& .${classes.wrapper}`]: {
    minWidth: 400
  },
  [`& .${classes.header}`]: {
    margin: 10
  },
  [`& .${classes.zoneName}`]: {
    fontSize: '2rem',
    textAlign: 'center',
    variant: 'h2'
  },
  [`& .${classes.centreName}`]: {
    fontSize: '1rem',
    textAlign: 'center',
    variant: 'h6'
  }
})

interface Props {
  className?: string
  selectedFireZone: FireZone | undefined
  fuelTypeInfo: Record<number, FireZoneThresholdFuelTypeArea[]>
  hfiElevationInfo: ElevationInfoByThreshold[]
  fireZoneAreas: FireZoneArea[]
}

const ZoneSummaryPanel = (props: Props) => {
  if (isUndefined(props.selectedFireZone)) {
    return <div></div>
  } else {
    return (
      <StyledGrid
        container
        alignItems={'center'}
        direction={'column'}
        spacing={2}
        className={`${props.className} ${classes.wrapper}`}
      >
        <Grid item>
          <Typography className={classes.zoneName}>{props.selectedFireZone.mof_fire_zone_name}</Typography>
          <Typography className={classes.centreName}>{props.selectedFireZone.mof_fire_centre_name}</Typography>
        </Grid>
        <Grid item>
          <CombustibleAreaViz
            fireZoneAreas={props.fireZoneAreas.filter(
              area => area.mof_fire_zone_id == props.selectedFireZone?.mof_fire_zone_id
            )}
          />
        </Grid>
        <Grid item>
          <FuelTypesBreakdown selectedFireZone={props.selectedFireZone} fuelTypeInfo={props.fuelTypeInfo} />
        </Grid>
        <Grid item>
          <ElevationInfoViz selectedFireZone={props.selectedFireZone} hfiElevationInfo={props.hfiElevationInfo} />
        </Grid>
      </StyledGrid>
    )
  }
}

export default React.memo(ZoneSummaryPanel)
