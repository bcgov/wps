import { makeStyles } from '@material-ui/core/styles'
import { WeatherStation } from 'api/hfiCalcAPI'
import { StationDaily } from 'api/hfiCalculatorAPI'
import { fireTableStyles } from 'app/theme'
import CalculatedCell from 'features/hfiCalculator/components/CalculatedCell'
import { DECIMAL_PLACES } from 'features/hfiCalculator/constants'
import React from 'react'

export interface WeeklyROSCellProps {
  daily: StationDaily
  station: WeatherStation
  isRowSelected: boolean
}

const useStyles = makeStyles({
  ...fireTableStyles
})
const WeeklyROSCell = ({ daily, station, isRowSelected }: WeeklyROSCellProps) => {
  const classes = useStyles()
  return (
    <CalculatedCell
      testid={`${station.code}-ros`}
      value={daily?.rate_of_spread?.toFixed(DECIMAL_PLACES)}
      error={false}
      className={
        isRowSelected ? classes.sectionSeperatorBorder : classes.unselectedStation
      }
    />
  )
}

export default React.memo(WeeklyROSCell)
