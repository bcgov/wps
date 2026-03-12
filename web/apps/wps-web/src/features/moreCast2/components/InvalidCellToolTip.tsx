import React from 'react'
import Tooltip from '@mui/material/Tooltip'
import { isEmpty } from 'lodash'
import { theme } from '@/app/theme'

export interface InvalidCellToolTipProps {
  invalid: string
  children: React.ReactNode
}

const InvalidCellToolTip = ({ invalid, children }: InvalidCellToolTipProps) => {
  return (
    <Tooltip
      data-testid="validation-tooltip"
      title={invalid}
      open={!isEmpty(invalid)}
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
