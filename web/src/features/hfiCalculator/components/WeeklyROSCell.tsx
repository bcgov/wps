import { TableCell } from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'
import { WeatherStation } from 'api/hfiCalcAPI'
import { StationDaily } from 'api/hfiCalculatorAPI'
import { fireTableStyles, UNSELECTED_STATION_COLOR } from 'app/theme'
import { DECIMAL_PLACES } from 'features/hfiCalculator/constants'
import React from 'react'

export interface WeeklyROSCellProps {
  daily: StationDaily
  station: WeatherStation
  isRowSelected: boolean
}

const useStyles = makeStyles({
  ...fireTableStyles,
  unselectedStation: {
    ...fireTableStyles.sectionSeperatorBorder,
    color: UNSELECTED_STATION_COLOR
  }
})
const WeeklyROSCell = ({ daily, station, isRowSelected }: WeeklyROSCellProps) => {
  const classes = useStyles()
  return (
    <TableCell
      data-testid={`${station.code}-ros`}
      className={
        isRowSelected ? classes.sectionSeperatorBorder : classes.unselectedStation
      }
    >
      {daily?.rate_of_spread?.toFixed(DECIMAL_PLACES)}
    </TableCell>
  )
}

export default React.memo(WeeklyROSCell)
