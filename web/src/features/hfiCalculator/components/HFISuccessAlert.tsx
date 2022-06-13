import makeStyles from '@mui/styles/makeStyles'
import { Alert, Snackbar } from '@mui/material'
import { useDispatch } from 'react-redux'
import React from 'react'
import { setChangeSaved } from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import { AppDispatch } from 'app/store'
import { setToggleSuccess } from 'features/hfiCalculator/slices/hfiReadySlice'

const message = 'Changes saved!'

export interface HFISuccessAlertProps {
  changeSaved: boolean
  readyToggleSuccess: boolean
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

const HFISuccessAlert = ({ changeSaved, readyToggleSuccess }: HFISuccessAlertProps) => {
  const classes = useStyles()

  const dispatch: AppDispatch = useDispatch()

  const handleClose = () => {
    if (changeSaved) {
      dispatch(setChangeSaved(false))
    }
    if (readyToggleSuccess) {
      dispatch(setToggleSuccess(false))
    }
  }

  return (
    <Snackbar
      data-testid="hfi-success-alert"
      open={changeSaved || readyToggleSuccess}
      autoHideDuration={6000}
      onClose={handleClose}
      anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
    >
      <Alert className={classes.alert} onClose={handleClose} severity="success">
        {message}
      </Alert>
    </Snackbar>
  )
}

export default React.memo(HFISuccessAlert)
