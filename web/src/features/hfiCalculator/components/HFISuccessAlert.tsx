import makeStyles from '@mui/styles/makeStyles'
import { Alert, Snackbar } from '@mui/material'
import { useDispatch, useSelector } from 'react-redux'
import { selectHFICalculatorState, selectHFIReadyState } from 'app/rootReducer'
import React from 'react'
import { setChangeSaved } from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import { AppDispatch } from 'app/store'
import { setToggleSuccess } from 'features/hfiCalculator/slices/hfiReadySlice'

const message = 'Changes saved!'

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

const HFISuccessAlert = () => {
  const classes = useStyles()

  const { readyToggleSuccess } = useSelector(selectHFIReadyState)
  const { changeSaved } = useSelector(selectHFICalculatorState)
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
