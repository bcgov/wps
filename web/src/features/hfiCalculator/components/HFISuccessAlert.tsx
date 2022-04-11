import { Alert } from '@material-ui/lab'
import { Snackbar } from '@material-ui/core'
import React from 'react'

export interface HFISuccessAlertProps {
  message: string | null
}

const HFISuccessAlert = ({ message }: HFISuccessAlertProps) => {
  const [open, setOpen] = React.useState(true)

  const handleClose = () => {
    setOpen(false)
  }

  return (
    <Snackbar
      open={open}
      autoHideDuration={6000}
      onClose={handleClose}
      anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
    >
      <Alert onClose={handleClose} severity="success">
        {message}
      </Alert>
    </Snackbar>
  )
}

export default React.memo(HFISuccessAlert)
