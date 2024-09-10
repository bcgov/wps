import { Typography } from '@mui/material'
import React from 'react'
import { isNull, isUndefined } from 'lodash'

interface CriticalHoursProps {
  start?: number
  end?: number
}

const CriticalHours = ({ start, end }: CriticalHoursProps) => {
  const formattedCriticalHours = isNull(start) || isUndefined(start) || isNull(end) || isUndefined(end) ? "-" : `${start}:00 - ${end}:00`
  return (
      <Typography sx={{ fontSize: '0.75rem' }} data-testid="critical-hours">
        {formattedCriticalHours}
      </Typography>
  )
}

export default React.memo(CriticalHours)
