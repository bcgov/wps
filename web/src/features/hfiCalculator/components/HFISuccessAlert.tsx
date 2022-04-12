import { makeStyles } from '@material-ui/core/styles'
import { Alert } from '@material-ui/lab'
import { Snackbar } from '@material-ui/core'
import React from 'react'

export interface HFISuccessAlertProps {
  message: string | null
}

const useStyles = makeStyles({
  alert: {
    backgroundColor: '#2E8540',
    color: 'white',
    '& .MuiAlert-icon': {
      color: 'white'
    },
    marginTop: 120
  }
})

const HFISuccessAlert = ({ message }: HFISuccessAlertProps) => {
  const classes = useStyles()
  const [open, setOpen] = React.useState(true)

  const handleClose = () => {
    setOpen(false)
  }

  return (
    <div>
      <Snackbar
        open={open}
        autoHideDuration={6000}
        onClose={handleClose}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <Alert className={classes.alert} onClose={handleClose} severity="success">
          {message}
        </Alert>
      </Snackbar>
    </div>
  )
}

export default React.memo(HFISuccessAlert)
