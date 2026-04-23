import React from 'react'
import Tooltip from '@mui/material/Tooltip'
import { isEmpty } from 'lodash'
import { theme } from '@wps/ui/theme'

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
      <span
        style={{
          display: 'flex',
          alignItems: 'center'
        }}
      >
        {children}
      </span>
    </Tooltip>
  )
}

export default React.memo(InvalidCellToolTip)
