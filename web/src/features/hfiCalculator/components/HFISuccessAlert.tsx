import { createStyles, makeStyles, Theme } from '@material-ui/core/styles'
import { Alert } from '@material-ui/lab'
import { Snackbar } from '@material-ui/core'
import React from 'react'

export interface HFISuccessAlertProps {
  message: string | null
}

const useStyles = makeStyles(
  { root: {} }
  // (theme: Theme) => {

  // }
  // createStyles({
  //   root: {
  //     marginTop: '200px'
  //     // width: '100%',
  //     // '& > * + *': {
  //     //   marginTop: theme.spacing(2)
  //     // },
  //     // marginBottom: theme.spacing(2)
  //   }
  // })
)

const HFISuccessAlert = ({ message }: HFISuccessAlertProps) => {
  const classes = useStyles()
  const [open, setOpen] = React.useState(true)

  const handleClose = () => {
    setOpen(false)
  }

  return (
    <div className={classes.root}>
      <Snackbar
        open={open}
        // autoHideDuration={6000}
        onClose={handleClose}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <Alert onClose={handleClose} severity="success">
          {message}
        </Alert>
      </Snackbar>
    </div>
  )
}

export default React.memo(HFISuccessAlert)
