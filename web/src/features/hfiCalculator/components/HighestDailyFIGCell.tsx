import { TableCell } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import { fireTableStyles, UNSELECTED_STATION_COLOR } from 'app/theme'
import React from 'react'

export interface WeeklyROSCellProps {
  testId?: string
  isRowSelected: boolean
}

const useStyles = makeStyles({
  ...fireTableStyles,
  unselectedStation: {
    ...fireTableStyles.sectionSeparatorBorder,
    color: UNSELECTED_STATION_COLOR
  }
})
const HighestDailyFIGCell = ({ testId, isRowSelected }: WeeklyROSCellProps) => {
  const classes = useStyles()
  return (
    <TableCell
      data-testid={testId}
      className={isRowSelected ? classes.sectionSeparatorBorder : classes.unselectedStation}
    />
  )
}

export default React.memo(HighestDailyFIGCell)
