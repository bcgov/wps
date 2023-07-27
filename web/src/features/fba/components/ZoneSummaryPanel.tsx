import React from 'react'
import { styled } from '@mui/material/styles'
import CombustibleAreaViz from 'features/fba/components/viz/CombustibleAreaViz'
import { Grid, Typography } from '@mui/material'
import { isUndefined } from 'lodash'
import { ElevationInfoByThreshold, FireZone, FireZoneArea, FireZoneThresholdFuelTypeArea } from 'api/fbaAPI'
import ElevationInfoViz from 'features/fba/components/viz/ElevationInfoViz'
import FuelTypesBreakdown from 'features/fba/components/viz/FuelTypesBreakdown'

const SidePanelGrid = styled(Grid)({
  minWidth: 400,
  overflowY: 'auto',
  maxHeight: '100%',
  padding: 0
})

const ZoneNameTyp = styled(Typography)({
  fontSize: '2rem',
  textAlign: 'center',
  variant: 'h2'
})

const CentreNameTyp = styled(Typography)({
  fontSize: '1rem',
  textAlign: 'center',
  variant: 'h6',
  paddingBottom: '2rem'
})

interface Props {
  selectedFireZone: FireZone | undefined
  fuelTypeInfo: Record<number, FireZoneThresholdFuelTypeArea[]>
  hfiElevationInfo: ElevationInfoByThreshold[]
  fireZoneAreas: FireZoneArea[]
}

const ZoneSummaryPanel = React.forwardRef((props: Props, ref: React.ForwardedRef<HTMLDivElement>) => {
  ZoneSummaryPanel.displayName = 'ZoneSummaryPanel'

  if (isUndefined(props.selectedFireZone)) {
    return <div></div>
  } else {
    return (
      <SidePanelGrid ref={ref}>
        <Grid container alignItems={'center'} direction={'column'}>
          <Grid item>
            <ZoneNameTyp>{props.selectedFireZone.mof_fire_zone_name}</ZoneNameTyp>
            <CentreNameTyp>{props.selectedFireZone.mof_fire_centre_name}</CentreNameTyp>
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
        </Grid>
      </SidePanelGrid>
    )
  }
})

export default React.memo(ZoneSummaryPanel)
