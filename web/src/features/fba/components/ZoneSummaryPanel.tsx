import React from 'react'
import { styled } from '@mui/material/styles'
import CombustibleAreaViz from 'features/fba/components/viz/CombustibleAreaViz'
import { Grid, IconButton, Typography } from '@mui/material'
import { isUndefined } from 'lodash'
import { ElevationInfoByThreshold, FireZone, FireZoneArea, FireZoneThresholdFuelTypeArea } from 'api/fbaAPI'
import ElevationInfoViz from 'features/fba/components/viz/ElevationInfoViz'
import FuelTypesBreakdown from 'features/fba/components/viz/FuelTypesBreakdown'
import CloseIcon from '@mui/icons-material/Close'

const SidePanelGrid = styled(Grid)({
  minWidth: 400,
  overflowY: 'scroll',
  maxHeight: '100%',
  padding: 0
})

const ZoneName = styled(Typography)({
  fontSize: '2rem',
  textAlign: 'center',
  variant: 'h2'
})

const CentreName = styled(Typography)({
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
  showSummaryPanel: boolean
  setShowSummaryPanel: React.Dispatch<React.SetStateAction<boolean>>
}

const ZoneSummaryPanel = React.forwardRef((props: Props, ref: React.ForwardedRef<HTMLDivElement>) => {
  ZoneSummaryPanel.displayName = 'ZoneSummaryPanel'

  const handleClose = () => {
    props.setShowSummaryPanel(false)
  }

  if (isUndefined(props.selectedFireZone) || !props.showSummaryPanel) {
    return <div></div>
  } else {
    return (
      <SidePanelGrid ref={ref}>
        <Grid container justifyContent="flex-end">
          <Grid item>
            <IconButton aria-label="Close" onClick={handleClose}>
              <CloseIcon />
            </IconButton>
          </Grid>
        </Grid>
        <Grid container alignItems={'center'} direction={'column'}>
          <Grid item>
            <ZoneName>{props.selectedFireZone.mof_fire_zone_name}</ZoneName>
            <CentreName>{props.selectedFireZone.mof_fire_centre_name}</CentreName>
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
