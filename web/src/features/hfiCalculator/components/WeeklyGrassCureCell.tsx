import { makeStyles } from '@material-ui/core/styles'
import { WeatherStation } from 'api/hfiCalcAPI'
import { StationDaily } from 'api/hfiCalculatorAPI'
import { isGrassFuelType } from 'features/fbaCalculator/utils'
import CalculatedCell from 'features/hfiCalculator/components/CalculatedCell'
import { DECIMAL_PLACES } from 'features/hfiCalculator/constants'
import React from 'react'

export interface WeeklyGrassCureCellProps {
  daily?: StationDaily
  station: WeatherStation
  isRowSelected: boolean
}

const useStyles = makeStyles({
  grassCureBorder: {
    borderLeft: '1px solid #C4C4C4'
  },
  unselectedStation: {
    color: 'rgba(0,0,0,0.54)'
  }
})
const WeeklyGrassCureCell = ({
  daily,
  station,
  isRowSelected
}: WeeklyGrassCureCellProps) => {
  const classes = useStyles()
  return (
    <CalculatedCell
      testid={`${station.code}-grass-cure`}
      value={daily?.grass_cure_percentage?.toFixed(DECIMAL_PLACES)}
      error={isGrassFuelType(station.station_props.fuel_type.abbrev)}
      className={isRowSelected ? undefined : classes.unselectedStation}
    />
  )
}

export default React.memo(WeeklyGrassCureCell)
