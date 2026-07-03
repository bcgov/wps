import { Alert, Snackbar } from '@mui/material'
import React from 'react'

interface PercentileSnackbarProps {
  autoHideDuration: number
  handleClose: () => void
  open: boolean
  message: string
}

const PercentileSnackbar = ({ autoHideDuration, handleClose, open, message }: PercentileSnackbarProps) => {
  const onClose = (_event: React.SyntheticEvent | Event, reason?: string) => {
    if (reason === 'clickaway') return
    handleClose()
  }

  return (
    <Snackbar
      anchorOrigin={{ horizontal: 'center', vertical: 'bottom' }}
      autoHideDuration={autoHideDuration}
      onClose={onClose}
      open={open}
    >
      <Alert onClose={handleClose} severity="warning" variant="filled">
        {message}
      </Alert>
    </Snackbar>
  )
}

export default React.memo(PercentileSnackbar)
