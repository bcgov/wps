import { Alert, Snackbar } from '@mui/material'
import { styled } from '@mui/material/styles'
import { theme } from '@wps/ui/theme'
import type { RootState } from 'app/rootReducer'
import type { AppDispatch } from 'app/store'
import { setChangeSaved } from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import { setToggleSuccess } from 'features/hfiCalculator/slices/hfiReadySlice'
import { isEqual } from 'lodash'
import React, { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'

const PREFIX = 'HFISuccessAlert'

const classes = {
  alert: `${PREFIX}-alert`
}

const StyledSnackbar = styled(Snackbar)({
  [`& .${classes.alert}`]: {
    backgroundColor: theme.palette.success.main,
    color: 'white',
    '& .MuiAlert-icon': {
      color: 'white'
    },
    marginTop: 120
  }
})

const message = 'Changes saved!'

const HFISuccessAlert = () => {
  const show = useSelector(
    (state: RootState) => state.hfiReady.readyToggleSuccess || state.hfiCalculatorDailies.changeSaved,
    isEqual
  )

  const [currentShowState, setCurrentShowState] = useState(false)

  useEffect(() => {
    setCurrentShowState(show)
  }, [show])

  const dispatch: AppDispatch = useDispatch()

  const handleClose = () => {
    dispatch(setChangeSaved(false))
    dispatch(setToggleSuccess(false))
  }

  return (
    <StyledSnackbar
      data-testid="hfi-success-alert"
      open={currentShowState}
      autoHideDuration={6000}
      onClose={handleClose}
      anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
    >
      <Alert className={classes.alert} onClose={handleClose} severity="success">
        {message}
      </Alert>
    </StyledSnackbar>
  )
}

export default React.memo(HFISuccessAlert)
