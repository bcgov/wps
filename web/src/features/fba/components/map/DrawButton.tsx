import React from 'react'
import { IconButton, Tooltip } from '@mui/material'
import HighlightAltIcon from '@mui/icons-material/HighlightAlt'

interface DrawProps {
  onClick: () => void
}

const DrawButton = ({ onClick }: DrawProps) => {
  return (
    <Tooltip title="Draw polygon">
      <IconButton onClick={onClick} sx={{ borderRadius: 0 }}>
        <HighlightAltIcon sx={{ backgroundColor: 'white' }} />
      </IconButton>
    </Tooltip>
  )
}

export default DrawButton
