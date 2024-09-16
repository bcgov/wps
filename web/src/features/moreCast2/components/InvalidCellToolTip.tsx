import React, { useState } from 'react'
import Tooltip from '@mui/material/Tooltip'
import { isEmpty } from 'lodash'
import { theme } from '@/app/theme'

export interface InvalidCellToolTipProps {
  error: string
  hovered?: boolean
  hoverOnly: boolean
  children: React.ReactNode
}

const InvalidCellToolTip = ({ error, hovered, hoverOnly, children }: InvalidCellToolTipProps) => {
  const open = (!isEmpty(error) && !hoverOnly) || (!isEmpty(error) && hoverOnly && hovered)

  return (
    <Tooltip
      data-testid="validation-tooltip"
      title={error}
      open={open}
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
