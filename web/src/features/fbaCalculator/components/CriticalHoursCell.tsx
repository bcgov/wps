import { TableCell } from '@mui/material'
import { styled } from '@mui/material/styles'
import { CriticalHoursHFI } from 'api/fbaCalcAPI'
import React from 'react'

const PREFIX = 'CriticalHoursCell'

const classes = {
  dataRow: `${PREFIX}-dataRow`
}

const StyledTableCell = styled(TableCell)({
  [`& .${classes.dataRow}`]: {
    height: '40px',
    paddingLeft: '8px',
    paddingRight: '8px'
  }
})

interface CriticalHoursCellProps {
  value: CriticalHoursHFI | undefined
  className?: string
}

export const formatCriticalHoursAsString = (criticalHours: CriticalHoursHFI | undefined | null): string | undefined => {
  if (criticalHours === undefined || criticalHours === null) {
    return undefined
  }
  return `${criticalHours.start}:00 - ${criticalHours.end}:00`
}
const CriticalHoursCell = (props: CriticalHoursCellProps) => {
  return (
    <StyledTableCell className={props.className ? props.className : classes.dataRow}>
      {formatCriticalHoursAsString(props.value)}
    </StyledTableCell>
  )
}

export default React.memo(CriticalHoursCell)
