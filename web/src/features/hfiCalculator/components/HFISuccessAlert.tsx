import { makeStyles } from '@material-ui/core/styles'
import { Alert } from '@material-ui/lab'
import { Collapse } from '@material-ui/core'
import React from 'react'

export interface HFISuccessAlertProps {
  message: string | null
}

const useStyles = makeStyles({
  alert: {
    width: '220px',
    margin: 'auto',
    backgroundColor: '#2E8540',
    color: 'white',
    '& .MuiAlert-icon': {
      color: 'white'
    }
  },
  '@global': {}
})

const HFISuccessAlert = ({ message }: HFISuccessAlertProps) => {
  const classes = useStyles()
  const [open, setOpen] = React.useState(true)

  const handleClose = () => {
    setOpen(false)
  }

  return (
    <div>
      {/* Ideally we should be using Snackbar (@material-ui/core) here, but with the warning message always being present it
      doesn't really work */}
      {/* <Snackbar
        open={open}
        autoHideDuration={6000}
        onClose={handleClose}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      > */}
      <Collapse in={open}>
        <Alert className={classes.alert} onClose={handleClose} severity="success">
          {message}
        </Alert>
      </Collapse>
      {/* </Snackbar> */}
    </div>
  )
}

export default React.memo(HFISuccessAlert)
