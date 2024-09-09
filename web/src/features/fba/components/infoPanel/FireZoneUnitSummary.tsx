import React from 'react'
import { Grid, Typography } from '@mui/material'
import { isNull, isUndefined } from 'lodash'
import { FireShape, FireZoneStats, FireZoneTPIStats } from 'api/fbaAPI'
import InfoAccordion from 'features/fba/components/infoPanel/InfoAccordion'
import ElevationStatus from 'features/fba/components/viz/ElevationStatus'
import { useTheme } from '@mui/material/styles'
import FuelSummary from 'features/fba/components/viz/FuelSummary'

interface FireZoneUnitSummaryProps {
  selectedFireZoneUnit: FireShape | undefined
  fireZoneStats: Record<number, FireZoneStats[]>
  fireZoneTPIStats: FireZoneTPIStats | null
}

const FireZoneUnitSummary = ({
  fireZoneStats,
  fireZoneTPIStats,
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

          <Grid item sx={{ paddingBottom: theme.spacing(2), width: '95%' }}>
            <FuelSummary selectedFireZoneUnit={selectedFireZoneUnit} fireZoneStats={fireZoneStats} />
          </Grid>
          <Grid item sx={{ width: '95%' }}>
            { isNull(fireZoneTPIStats) || fireZoneTPIStats.valley_bottom + fireZoneTPIStats.mid_slope + fireZoneTPIStats.upper_slope === 0 ? (
              <Typography>
                No elevation information available.
              </Typography>
            ) : (
            <ElevationStatus
              upper={fireZoneTPIStats.upper_slope}
              mid={fireZoneTPIStats.mid_slope}
              bottom={fireZoneTPIStats.valley_bottom}
            ></ElevationStatus>)}
          </Grid>
        </Grid>
      </InfoAccordion>
    </div>
  )
}

export default React.memo(FireZoneUnitSummary)
