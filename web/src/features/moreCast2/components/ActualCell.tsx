import React, { useState } from 'react'
import { TextField, Tooltip } from '@mui/material'
import { theme } from 'app/theme'
import { GridRenderCellParams } from '@mui/x-data-grid-pro'

interface ActualCellProps {
  missingActual: boolean
  value: Pick<GridRenderCellParams, 'formattedValue'>
}

const MISSING_ACTUAL_MESSAGE = 'Observation not available from WF1.'

const ActualCell = ({ missingActual, value }: ActualCellProps) => {
  const [open, setOpen] = useState<boolean>(false)
  const handleClose = () => {
    setOpen(false)
  }
  const handleOpen = () => {
    if (missingActual) {
      setOpen(true)
    }
  }
  return (
    <Tooltip
      open={open}
      onClose={handleClose}
      onOpen={handleOpen}
      placement="bottom-start"
      title={MISSING_ACTUAL_MESSAGE}
    >
      <TextField
        sx={{
          backgroundColor: theme.palette.common.white,
          border: '2px',
          borderColor: theme.palette.error.main,
          borderStyle: missingActual ? 'solid' : 'none',
          borderRadius: 1
        }}
        disabled={true}
        size="small"
        value={value}
      ></TextField>
    </Tooltip>
  )
}

export default React.memo(ActualCell)
