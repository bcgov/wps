import { TableCell } from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'
import { StationDaily } from 'api/hfiCalculatorAPI'
import { fireTableStyles, UNSELECTED_STATION_COLOR } from 'app/theme'
import { DECIMAL_PLACES } from 'features/hfiCalculator/constants'
import React from 'react'

export interface WeeklyROSCellProps {
  daily?: StationDaily
  testId?: string
  error: boolean
  isRowSelected: boolean
}

const useStyles = makeStyles({
  ...fireTableStyles,
  unselectedStation: {
    ...fireTableStyles.sectionSeparatorBorder,
    color: UNSELECTED_STATION_COLOR
  }
})
const WeeklyROSCell = ({ daily, testId, isRowSelected, error }: WeeklyROSCellProps) => {
  const classes = useStyles()
  return (
    <TableCell
      data-testid={testId}
      className={
        isRowSelected ? classes.sectionSeparatorBorder : classes.unselectedStation
      }
    >
      {error ? '' : daily?.rate_of_spread?.toFixed(DECIMAL_PLACES)}
    </TableCell>
  )
}

export default React.memo(WeeklyROSCell)
