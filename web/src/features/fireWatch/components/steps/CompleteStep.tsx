import { Box, CircularProgress, Step, Typography, useTheme } from '@mui/material'
import { useSelector } from 'react-redux'
import { fireWatch as fireWatchState, RootState } from 'app/rootReducer'
import { useEffect } from 'react'
import { FORM_MAX_WIDTH } from '@/features/fireWatch/constants'

interface CompleteStepProps {
  isEditMode?: boolean
  isLoading?: boolean
}

const CompleteStep = ({ isEditMode, isLoading }: CompleteStepProps) => {
  const theme = useTheme()
  const { fireWatchSubmitError } = useSelector(fireWatchState)
  const { error: updateError } = useSelector((state: RootState) => state.burnForecasts)

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
        {isLoading && (
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
            <CircularProgress />
          </Box>
        )}
        {isEditMode && !isLoading && updateError && (
          <Typography sx={{ fontWeight: 'bold' }} variant="body1" color="error">
            An error occurred while updating the fire watch.
          </Typography>
        )}
        {isEditMode && !isLoading && !updateError && (
          <Typography sx={{ fontWeight: 'bold' }} variant="body1">
            The fire watch has been successfully updated.
          </Typography>
        )}
        {!isEditMode && !isLoading && fireWatchSubmitError && (
          <Typography sx={{ fontWeight: 'bold' }} variant="body1" color="error">
            An error occurred while submitting the prescribed fire information.
          </Typography>
        )}
        {!isEditMode && !isLoading && !fireWatchSubmitError && (
          <Typography sx={{ fontWeight: 'bold' }} variant="body1">
            A new fire watch has been successfully submitted.
          </Typography>
        )}
      </Box>
    </Step>
  )
}

export default CompleteStep
