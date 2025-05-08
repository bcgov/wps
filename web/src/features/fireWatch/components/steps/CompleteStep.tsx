import { FORM_MAX_WIDTH } from '@/features/fireWatch/components/CreateFireWatch'
import { Box, CircularProgress, Step, Typography, useTheme } from '@mui/material'
import { useSelector } from 'react-redux'
import { fireWatch as fireWatchState } from 'app/rootReducer'
import { useEffect } from 'react'

const CompleteStep = () => {
  const theme = useTheme()
  const { fireWatchSubmitting, fireWatchSubmitError } = useSelector(fireWatchState)

  useEffect(() => {
    if (fireWatchSubmitError) {
      console.error(fireWatchSubmitError)
    }
  }, [fireWatchSubmitError])

  return (
    <Step>
      <Box
        sx={{ display: 'flex', flexDirection: 'column', maxWidth: `${FORM_MAX_WIDTH}px`, padding: theme.spacing(4) }}
      >
        {fireWatchSubmitting && <CircularProgress />}
        {!fireWatchSubmitting && fireWatchSubmitError && (
          <Typography sx={{ fontWeight: 'bold' }} variant="body1" color="error">
            An error occurred while submitting the prescribed fire information.
          </Typography>
        )}
        {!fireWatchSubmitting && !fireWatchSubmitError && (
          <Typography sx={{ fontWeight: 'bold' }} variant="body1">
            A new fire watch has been successfully submitted. You will receive a notification at the provided email each
            time the burn comes into prescription.
          </Typography>
        )}
      </Box>
    </Step>
  )
}

export default CompleteStep
