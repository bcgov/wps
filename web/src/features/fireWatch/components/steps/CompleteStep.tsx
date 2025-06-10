import { FORM_MAX_WIDTH } from '@/features/fireWatch/components/CreateFireWatch'
import { Box, CircularProgress, Step, Typography, useTheme } from '@mui/material'
import { useSelector } from 'react-redux'
import { fireWatch as fireWatchState, RootState } from 'app/rootReducer'
import { useEffect } from 'react'

interface CompleteStepProps {
  isEditMode?: boolean
}

const CompleteStep = ({ isEditMode }: CompleteStepProps) => {
  const theme = useTheme()
  const { fireWatchSubmitting, fireWatchSubmitError } = useSelector(fireWatchState)
  const { loading: updateLoading, error: updateError } = useSelector((state: RootState) => state.burnForecasts)

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
        {(fireWatchSubmitting || updateLoading) && (
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
            <CircularProgress />
          </Box>
        )}
        {isEditMode && !updateLoading && updateError && (
          <Typography sx={{ fontWeight: 'bold' }} variant="body1" color="error">
            An error occurred while updating the fire watch.
          </Typography>
        )}
        {isEditMode && !updateLoading && !updateError && (
          <Typography sx={{ fontWeight: 'bold' }} variant="body1">
            The fire watch has been successfully updated.
          </Typography>
        )}
        {!isEditMode && !fireWatchSubmitting && fireWatchSubmitError && (
          <Typography sx={{ fontWeight: 'bold' }} variant="body1" color="error">
            An error occurred while submitting the prescribed fire information.
          </Typography>
        )}
        {!isEditMode && !fireWatchSubmitting && !fireWatchSubmitError && (
          <Typography sx={{ fontWeight: 'bold' }} variant="body1">
            A new fire watch has been successfully submitted.
          </Typography>
        )}
      </Box>
    </Step>
  )
}

export default CompleteStep
