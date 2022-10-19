import { TableCell } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import { CriticalHoursHFI } from 'api/fbaCalcAPI'
import React from 'react'

interface CriticalHoursCellProps {
  value: CriticalHoursHFI | undefined
  className?: string
}

const useStyles = makeStyles({
  dataRow: {
    height: '40px',
    paddingLeft: '8px',
    paddingRight: '8px'
  }
})

export const formatCriticalHoursAsString = (criticalHours: CriticalHoursHFI | undefined | null): string | undefined => {
  if (criticalHours === undefined || criticalHours === null) {
    return undefined
  }
  return `${criticalHours.start}:00 - ${criticalHours.end}:00`
}
const CriticalHoursCell = (props: CriticalHoursCellProps) => {
  const classes = useStyles()

  return (
    <TableCell className={props.className ? props.className : classes.dataRow}>
      {formatCriticalHoursAsString(props.value)}
    </TableCell>
  )
}

export default React.memo(CriticalHoursCell)
