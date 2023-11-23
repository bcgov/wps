import React from 'react'
import { Alert, Snackbar } from '@mui/material'

interface PercentileSnackbarProps {
  autoHideDuration: number
  handleClose: () => void
  open: boolean
  message: string
}

const PercentileSnackbar = ({ autoHideDuration, handleClose, open, message }: PercentileSnackbarProps) => {
  return (
    <Snackbar
      anchorOrigin={{ horizontal: 'center', vertical: 'bottom' }}
      autoHideDuration={autoHideDuration}
      onClose={handleClose}
      open={open}
    >
      <Alert onClose={handleClose} severity="warning" variant="filled">
        {message}
      </Alert>
    </Snackbar>
  )
}

export default React.memo(PercentileSnackbar)
