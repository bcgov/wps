import React from 'react'
import { Grid, Typography } from '@mui/material'
import { isNull, isUndefined } from 'lodash'
import { FireShape, FireZoneTPIStats, FireZoneThresholdFuelTypeArea } from 'api/fbaAPI'
import ElevationStatus from 'features/fba/components/viz/ElevationStatus'
import { useTheme } from '@mui/material/styles'
import FuelSummary from 'features/fba/components/viz/FuelSummary'

interface FireZoneUnitSummaryProps {
  selectedFireZoneUnit: FireShape | undefined
  fuelTypeInfo: Record<number, FireZoneThresholdFuelTypeArea[]>
  fireZoneTPIStats: FireZoneTPIStats | undefined
}

const FireZoneUnitSummary = ({ fuelTypeInfo, fireZoneTPIStats, selectedFireZoneUnit }: FireZoneUnitSummaryProps) => {
  const theme = useTheme()

  if (isUndefined(selectedFireZoneUnit)) {
    return <div data-testid="fire-zone-unit-summary-empty"></div>
  }
  return (
    <div data-testid="fire-zone-unit-summary">
      <Grid
        container
        alignItems={'center'}
        direction={'column'}
        sx={{ paddingBottom: theme.spacing(2), paddingTop: theme.spacing(2) }}
      >
        <Grid item sx={{ paddingBottom: theme.spacing(2), width: '95%' }}>
          <FuelSummary selectedFireZoneUnit={selectedFireZoneUnit} fuelTypeInfo={fuelTypeInfo} />
        </Grid>
        <Grid item sx={{ width: '95%' }}>
          {isUndefined(fireZoneTPIStats) ||
          fireZoneTPIStats.valley_bottom + fireZoneTPIStats.mid_slope + fireZoneTPIStats.upper_slope === 0 ? (
            <Typography>No elevation information available.</Typography>
          ) : (
            <ElevationStatus
              upper={fireZoneTPIStats.upper_slope}
              mid={fireZoneTPIStats.mid_slope}
              bottom={fireZoneTPIStats.valley_bottom}
            ></ElevationStatus>
          )}
        </Grid>
      </Grid>
    </div>
  )
}

export default React.memo(FireZoneUnitSummary)
