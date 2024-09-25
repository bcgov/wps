import React from 'react'
import Tooltip from '@mui/material/Tooltip'
import { isEmpty } from 'lodash'
import { theme } from '@/app/theme'

export interface InvalidCellToolTipProps {
  error: string
  children: React.ReactNode
}

const InvalidCellToolTip = ({ error, children }: InvalidCellToolTipProps) => {
  return (
    <Tooltip
      data-testid="validation-tooltip"
      title={error}
      open={!isEmpty(error)}
      arrow
      sx={{
        '& .MuiTooltip-tooltip': {
          backgroundColor: theme.palette.error.main,
          color: theme.palette.error.contrastText
        }
      }}
    >
      <span>{children}</span>
    </Tooltip>
  )
}

export default React.memo(InvalidCellToolTip)
