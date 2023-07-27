import React from 'react'
import { Alert, AlertColor, Snackbar } from '@mui/material'

interface MoreCast2SnackbarProps {
  autoHideDuration: number
  handleClose: () => void
  open: boolean
  message: string
  severity: AlertColor
}

const MoreCast2Snackbar = ({ autoHideDuration, handleClose, open, message, severity }: MoreCast2SnackbarProps) => {
  return (
    <Snackbar
      anchorOrigin={{ horizontal: 'center', vertical: 'bottom' }}
      autoHideDuration={autoHideDuration}
      onClose={handleClose}
      open={open}
    >
      <Alert onClose={handleClose} severity={severity} variant="filled">
        {message}
      </Alert>
    </Snackbar>
  )
}

export default React.memo(MoreCast2Snackbar)
