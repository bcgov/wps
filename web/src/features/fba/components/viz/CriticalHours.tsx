import { Typography } from '@mui/material'
import React from 'react'
import { isNil, isNull, isUndefined } from 'lodash'

interface CriticalHoursProps {
  start?: number
  end?: number
}

const CriticalHours = ({ start, end }: CriticalHoursProps) => {
  const extendsNextDay = !isNil(start) && !isNil(end) && end <= start
  const paddedStartTime = String(start).padStart(2, '0')
  const paddedEndTime = String(end).padStart(2, '0')
  const formattedEndTime = `${paddedEndTime}:00${extendsNextDay ? '+1' : ''}`

  const formattedCriticalHours = isNil(start) || isNil(end) ? '-' : `${paddedStartTime}:00 - ${formattedEndTime}`
  return (
    <Typography sx={{ fontSize: '0.75rem' }} data-testid="critical-hours">
      {formattedCriticalHours}
    </Typography>
  )
}

export default React.memo(CriticalHours)
