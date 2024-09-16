import React, { useState } from 'react'
import Tooltip from '@mui/material/Tooltip'
import { isEmpty } from 'lodash'
import { theme } from '@/app/theme'

export interface InvalidCellToolTipProps {
  error: string
  hoverOnly: boolean
  children: React.ReactNode
}

const InvalidCellToolTip = ({ error, hoverOnly, children }: InvalidCellToolTipProps) => {
  const [isHovered, setIsHovered] = useState(false)

  const handleMouseEnter = () => {
    setIsHovered(true)
  }

  const handleMouseLeave = () => {
    setIsHovered(false)
  }

  const open = (!isEmpty(error) && !hoverOnly) || (!isEmpty(error) && hoverOnly && isHovered)

  return (
    <Tooltip
      data-testid="validation-tooltip"
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
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
