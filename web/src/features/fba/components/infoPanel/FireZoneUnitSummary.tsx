import React from 'react'
import CombustibleAreaViz from 'features/fba/components/viz/CombustibleAreaViz'
import { Grid } from '@mui/material'
import { isUndefined } from 'lodash'
import { ElevationInfoByThreshold, FireShape, FireShapeArea, FireZoneThresholdFuelTypeArea } from 'api/fbaAPI'
import FuelTypesBreakdown from 'features/fba/components/viz/FuelTypesBreakdown'
import InfoAccordion from 'features/fba/components/infoPanel/InfoAccordion'
import ElevationStatus from 'features/fba/components/viz/ElevationStatus'
import { useTheme } from '@mui/material/styles'
import { HFIRiskStatus } from 'features/fba/components/viz/ElevationFlag'

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
          <Grid item sx={{ width: '100%' }}>
            <ElevationStatus
              bottom={HFIRiskStatus.WARNING}
              mid={HFIRiskStatus.ADVISORY}
              upper={HFIRiskStatus.LOW}
            ></ElevationStatus>
          </Grid>
          <Grid item>
            <CombustibleAreaViz
              fireZoneAreas={fireShapeAreas.filter(area => area.fire_shape_id == selectedFireZoneUnit?.fire_shape_id)}
            />
          </Grid>
          <Grid item>
            <FuelTypesBreakdown selectedFireZone={selectedFireZoneUnit} fuelTypeInfo={fuelTypeInfo} />
          </Grid>
        </Grid>
      </InfoAccordion>
    </div>
  )
}

export default React.memo(FireZoneUnitSummary)
