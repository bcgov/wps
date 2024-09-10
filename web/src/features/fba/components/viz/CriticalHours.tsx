import { Typography } from '@mui/material'
import React from 'react'
import { isUndefined } from 'lodash'

interface CriticalHoursProps {
  start?: number
  end?: number
}

const CriticalHours = ({ start, end }: CriticalHoursProps) => {
  return (
      <Typography sx={{ fontSize: '0.75rem' }} data-testid="critical-hours">
        {isUndefined(start) || isUndefined(end) ? "-" : `${start}:00 - ${end}:00`}
      </Typography>
  )
}

export default React.memo(CriticalHours)
