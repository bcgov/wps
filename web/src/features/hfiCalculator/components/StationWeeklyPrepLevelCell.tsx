import { TableCell } from '@material-ui/core'
import { WeatherStation } from 'api/hfiCalcAPI'
import { StationDaily } from 'api/hfiCalculatorAPI'
import { calculateMeanIntensity } from 'features/hfiCalculator/components/meanIntensity'
import { calculatePrepLevel } from 'features/hfiCalculator/components/prepLevel'
import React from 'react'

export interface StationWeeklyPrepLevelCellProps {
  station: WeatherStation
  dailies: StationDaily[]
}

const StationWeeklyPrepLevelCell = (props: StationWeeklyPrepLevelCellProps) => {
  const meanIntensityGroup = calculateMeanIntensity(props.dailies)
  return (
    <TableCell data-testid={'daily-prep-level'}>
      {calculatePrepLevel(meanIntensityGroup)}
    </TableCell>
  )
}

export default React.memo(StationWeeklyPrepLevelCell)
