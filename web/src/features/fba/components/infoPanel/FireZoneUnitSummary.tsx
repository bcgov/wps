import React from 'react'
import { Grid, Typography } from '@mui/material'
import { isNil, isUndefined } from 'lodash'
import { FireShape, FireZoneTPIStats, FireZoneFuelStats } from 'api/fbaAPI'
import ElevationStatus from 'features/fba/components/viz/ElevationStatus'
import { useTheme } from '@mui/material/styles'
import FuelSummary from '@/features/fba/components/viz/FuelSummary'

interface FireZoneUnitSummaryProps {
  selectedFireZoneUnit: FireShape | undefined
  fireZoneFuelStats: Record<number, FireZoneFuelStats[]>
  fireZoneTPIStats: FireZoneTPIStats | undefined
}

function hasRequiredFields(stats: FireZoneTPIStats): stats is Required<FireZoneTPIStats> {
  return (
    !isNil(stats.mid_slope_hfi) &&
    !isNil(stats.mid_slope_tpi) &&
    !isNil(stats.upper_slope_hfi) &&
    !isNil(stats.upper_slope_tpi) &&
    !isNil(stats.valley_bottom_hfi) &&
    !isNil(stats.valley_bottom_tpi)
  )
}

const FireZoneUnitSummary = ({
  fireZoneFuelStats,
  fireZoneTPIStats,
  selectedFireZoneUnit
}: FireZoneUnitSummaryProps) => {
  const theme = useTheme()

  if (isUndefined(selectedFireZoneUnit)) {
    return <div data-testid="fire-zone-unit-summary-empty"></div>
  }
  return (
    <div data-testid="fire-zone-unit-summary">
      <Grid container alignItems={'center'} direction={'column'} sx={{ paddingBottom: theme.spacing(2) }}>
        <Grid item sx={{ paddingBottom: theme.spacing(2), width: '95%' }}>
          <FuelSummary selectedFireZoneUnit={selectedFireZoneUnit} fireZoneFuelStats={fireZoneFuelStats} />
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
