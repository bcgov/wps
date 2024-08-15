import React, { useEffect, useState } from 'react'
import { Grid, Typography } from '@mui/material'
import { isNull, isUndefined } from 'lodash'
import { FireShape, FireShapeArea, FireZoneTPIStats, FireZoneThresholdFuelTypeArea } from 'api/fbaAPI'
import InfoAccordion from 'features/fba/components/infoPanel/InfoAccordion'
import ElevationStatus from 'features/fba/components/viz/ElevationStatus'
import { useTheme } from '@mui/material/styles'
import FuelSummary from 'features/fba/components/viz/FuelSummary'

interface FireZoneUnitSummaryProps {
  selectedFireZoneUnit: FireShape | undefined
  fuelTypeInfo: Record<number, FireZoneThresholdFuelTypeArea[]>
  fireZoneTPIStats: FireZoneTPIStats | null
  fireShapeAreas: FireShapeArea[]
}

const FireZoneUnitSummary = ({
  fireShapeAreas,
  fuelTypeInfo,
  fireZoneTPIStats,
  selectedFireZoneUnit
}: FireZoneUnitSummaryProps) => {
  const theme = useTheme()
  const [midSlope, setMidSlope] = useState<number>(0)
  const [upperSlope, setUpperSlope] = useState<number>(0)
  const [valleyBottom, setValleyBottom] = useState<number>(0)

  useEffect(() => {
    if (!isNull(fireZoneTPIStats)) {
      const total = fireZoneTPIStats.mid_slope + fireZoneTPIStats.upper_slope + fireZoneTPIStats.valley_bottom
      setMidSlope(Math.round(fireZoneTPIStats.mid_slope/total*100))
      setUpperSlope(Math.round(fireZoneTPIStats.upper_slope/total*100))
      setValleyBottom(Math.round(fireZoneTPIStats.valley_bottom/total*100))
    }
  }, [fireZoneTPIStats])

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
            { Object.keys(fuelTypeInfo).length === 0 ? (
              <Typography>
                No fuel type information available.
              </Typography>
          ): (
            <FuelSummary selectedFireZoneUnit={selectedFireZoneUnit} fuelTypeInfo={fuelTypeInfo} />)}
          </Grid>
          <Grid item sx={{ width: '95%' }}>
            { isNull(fireZoneTPIStats) ? (
              <Typography>
                No elevation information available.
              </Typography>
            ) : (
            <ElevationStatus
              upper={upperSlope}
              mid={midSlope}
              bottom={valleyBottom}
            ></ElevationStatus>)}
          </Grid>
        </Grid>
      </InfoAccordion>
    </div>
  )
}

export default React.memo(FireZoneUnitSummary)
