import React from 'react'
import { Grid } from '@mui/material'
import { isUndefined } from 'lodash'
import { ElevationInfoByThreshold, FireShape, FireShapeArea, FireZoneThresholdFuelTypeArea } from 'api/fbaAPI'
import ElevationInfoViz from 'features/fba/components/viz/ElevationInfoViz'
import InfoAccordion from 'features/fba/components/infoPanel/InfoAccordion'
import { useTheme } from '@mui/material/styles'
import FuelSummary from 'features/fba/components/viz/FuelSummary'

interface FireZoneUnitSummaryProps {
  selectedFireZoneUnit: FireShape | undefined
  fuelTypeInfo: Record<number, FireZoneThresholdFuelTypeArea[]>
  hfiElevationInfo: ElevationInfoByThreshold[]
  fireShapeAreas: FireShapeArea[]
}

const FireZoneUnitSummary = ({
  fireShapeAreas,
  fuelTypeInfo,
  hfiElevationInfo,
  selectedFireZoneUnit
}: FireZoneUnitSummaryProps) => {
  const theme = useTheme()

  if (isUndefined(selectedFireZoneUnit)) {
    return <div data-testid="fire-zone-unit-summary-empty"></div>
  }
  return (
    <div data-testid="fire-zone-unit-summary">
      <InfoAccordion defaultExpanded={true} title={selectedFireZoneUnit.mof_fire_zone_name}>
        <Grid
          container
          alignItems={'center'}
          direction={'column'}
          sx={{ paddingBottom: theme.spacing(2), paddingTop: theme.spacing(2) }}
        >
          <Grid item sx={{ width: '95%' }}>
            <FuelSummary selectedFireZoneUnit={selectedFireZoneUnit} fuelTypeInfo={fuelTypeInfo} />
          </Grid>
          <Grid item>
            <ElevationInfoViz selectedFireZone={selectedFireZoneUnit} hfiElevationInfo={hfiElevationInfo} />
          </Grid>
        </Grid>
      </InfoAccordion>
    </div>
  )
}

export default React.memo(FireZoneUnitSummary)
