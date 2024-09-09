import { Tooltip, Typography } from '@mui/material'
import React from 'react'
import { isUndefined } from 'lodash'

interface CriticalHoursProps {
  start?: number
  end?: number
}

const CriticalHours = ({ start, end }: CriticalHoursProps) => {
  return (
    <Tooltip title={'Critical hours'} placement="right">
      <Typography sx={{ fontSize: '0.75rem' }} data-testid="critical-hours">
        {isUndefined(start) || isUndefined(end) ? "-" : `${start} - ${end}`}
      </Typography>
    </Tooltip>
  )
}

export default React.memo(CriticalHours)
