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

function hasRequiredFields(stats: FireZoneTPIStats): stats is Required<FireZoneTPIStats> {
  return (
    !isUndefined(stats.mid_slope) &&
    !isNull(stats.mid_slope) &&
    !isUndefined(stats.upper_slope) &&
    !isNull(stats.upper_slope) &&
    !isUndefined(stats.valley_bottom) &&
    !isNull(stats.valley_bottom) &&
    stats.mid_slope + stats.upper_slope + stats.mid_slope !== 0
  )
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
          {fireZoneTPIStats && hasRequiredFields(fireZoneTPIStats) ? (
            <ElevationStatus tpiStats={fireZoneTPIStats}></ElevationStatus>
          ) : (
            <Typography>No elevation information available.</Typography>
          )}
        </Grid>
      </Grid>
    </div>
  )
}

export default React.memo(FireZoneUnitSummary)
