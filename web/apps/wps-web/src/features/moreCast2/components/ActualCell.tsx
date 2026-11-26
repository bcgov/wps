import { TextField, Tooltip } from '@mui/material'
import type { GridRenderCellParams } from '@mui/x-data-grid-pro'
import { theme } from '@wps/ui/theme'
import React, { useState } from 'react'

interface ActualCellProps {
  missingActual: boolean
  value: Pick<GridRenderCellParams, 'formattedValue'>
}

const MISSING_ACTUAL_MESSAGE = 'Actual not available from WF1.'

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
        data-testid="actual-cell"
        sx={{
          backgroundColor: theme.palette.common.white,
          border: '2px',
          borderColor: theme.palette.error.main,
          borderStyle: missingActual ? 'solid' : 'none',
          borderRadius: 1,
          // observations stay read only without fading into the model reference values
          '& .MuiInputBase-input.Mui-disabled': {
            color: theme.palette.text.primary,
            WebkitTextFillColor: theme.palette.text.primary,
            opacity: 1,
            fontWeight: 600
          }
        }}
        disabled={true}
        size="small"
        value={value}
      ></TextField>
    </Tooltip>
  )
}

export default React.memo(ActualCell)
