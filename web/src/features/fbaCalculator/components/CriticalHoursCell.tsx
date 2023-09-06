import { CriticalHoursHFI } from 'api/fbaCalcAPI'
import { DataTableCell } from 'features/hfiCalculator/components/StyledPlanningAreaComponents'
import React from 'react'

const PREFIX = 'CriticalHoursCell'

const classes = {
  dataRow: `${PREFIX}-dataRow`
}

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
    <DataTableCell className={props.className ? props.className : classes.dataRow}>
      {formatCriticalHoursAsString(props.value)}
    </DataTableCell>
  )
}

export default CriticalHoursCell
