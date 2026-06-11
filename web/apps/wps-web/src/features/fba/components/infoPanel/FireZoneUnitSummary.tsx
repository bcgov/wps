import { Box, Stack, Typography } from '@mui/material'
import { useTheme } from '@mui/material/styles'
import type { FireShape, FireZoneFuelStats, FireZoneTPIStats } from '@wps/api/fbaAPI'
import ElevationStatus from 'features/fba/components/viz/ElevationStatus'
import { isNil, isUndefined } from 'lodash'
import React from 'react'
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
      <Stack
        sx={{
          alignItems: 'center',
          paddingBottom: theme.spacing(2)
        }}
      >
        <Box sx={{ paddingBottom: theme.spacing(2), width: '95%' }}>
          <FuelSummary selectedFireZoneUnit={selectedFireZoneUnit} fireZoneFuelStats={fireZoneFuelStats} />
        </Box>
        <Box sx={{ width: '95%' }}>
          {fireZoneTPIStats && hasRequiredFields(fireZoneTPIStats) ? (
            <ElevationStatus tpiStats={fireZoneTPIStats}></ElevationStatus>
          ) : (
            <Typography>No elevation information available.</Typography>
          )}
        </Box>
      </Stack>
    </div>
  )
}

export default React.memo(FireZoneUnitSummary)
