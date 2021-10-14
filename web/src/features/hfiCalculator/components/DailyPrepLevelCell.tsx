import { TableCell } from '@material-ui/core'
import { WeatherStation } from 'api/hfiCalcAPI'
import { StationDaily } from 'api/hfiCalculatorAPI'
import { calculateMeanIntensityGroup } from 'features/hfiCalculator/components/meanIntensity'
import { calculatePrepLevel } from 'features/hfiCalculator/components/prepLevel'
import { StationWithDaily } from 'features/hfiCalculator/util'
import React from 'react'

export interface DailyPrepLevelCellProps {
  station: WeatherStation
  dailies: StationDaily[] | undefined
}

const DailyPrepLevelCell = (props: DailyPrepLevelCellProps) => {
  const stationWithDailies: StationWithDaily[] = props.dailies
    ? props.dailies?.map(daily => ({
        station: props.station,
        daily
      }))
    : []

  const meanIntensityGroup = calculateMeanIntensityGroup(stationWithDailies, [
    props.station.code
  ])
  return (
    <TableCell data-testid={'daily-prep-level'}>
      {calculatePrepLevel(meanIntensityGroup)}
    </TableCell>
  )
}

export default React.memo(DailyPrepLevelCell)
