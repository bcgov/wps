import { TableCell } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import { StationDaily } from 'api/hfiCalculatorAPI'
import { fireTableStyles, UNSELECTED_STATION_COLOR } from 'app/theme'
import { DECIMAL_PLACES } from 'features/hfiCalculator/constants'
import React from 'react'

export interface WeeklyROSCellProps {
  daily?: StationDaily
  testId?: string
  error: boolean
  isRowSelected: boolean
  isFirstDayOfPrepPeriod: boolean
}

const useStyles = makeStyles({
  ...fireTableStyles,
  unselectedStation: {
    color: UNSELECTED_STATION_COLOR
  }
})
const WeeklyROSCell = ({ daily, testId, isRowSelected, error, isFirstDayOfPrepPeriod }: WeeklyROSCellProps) => {
  const dataValue = error ? '' : daily?.rate_of_spread?.toFixed(DECIMAL_PLACES)

  const classes = useStyles()
  return (
    <TableCell
      data-testid={testId}
      className={`${!isRowSelected ? classes.unselectedStation : undefined} ${
        !isFirstDayOfPrepPeriod ? classes.sectionSeparatorBorder : undefined
      }`}
    >
      {dataValue}
    </TableCell>
  )
}

export default React.memo(WeeklyROSCell)
