import { getStations, StationSource } from '@/api/stationAPI'
import { AppDispatch } from '@/app/store'
import CompleteStep from '@/features/fireWatch/components/steps/CompleteStep'
import FireBehvaiourIndicesStep from '@/features/fireWatch/components/steps/FireBehaviourIndicesStep'
import FuelStep from '@/features/fireWatch/components/steps/FuelStep'
import InfoStep from '@/features/fireWatch/components/steps/InfoStep'
import LocationStep from '@/features/fireWatch/components/steps/LocationStep'
import ReviewSubmitStep from '@/features/fireWatch/components/steps/ReviewSubmitStep'
import WeatherParametersStep from '@/features/fireWatch/components/steps/WeatherParametersStep'
import { FireWatch } from '@/features/fireWatch/interfaces'
import { submitNewFireWatch } from '@/features/fireWatch/slices/fireWatchSlice'
import { updateFireWatch } from '../slices/burnForecastSlice'
import { getBlankFireWatch } from '@/features/fireWatch/utils'
import { Box, Button, Step, StepLabel, Stepper, Typography, useTheme } from '@mui/material'
import { fetchFireWatchFireCentres } from 'features/fireWatch/slices/fireWatchFireCentresSlice'
import { fetchWxStations } from 'features/stations/slices/stationsSlice'
import { useEffect, useRef, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { FORM_MAX_WIDTH } from '@/features/fireWatch/constants'
import { fireWatch as fireWatchState, RootState } from '@/app/rootReducer'

interface CreateFireWatchProps {
  fireWatch?: FireWatch
  activeStep?: number
  onCloseModal?: () => void
}

const CreateFireWatch = ({
  fireWatch: initialFireWatch,
  activeStep: initialActiveStep,
  onCloseModal
}: CreateFireWatchProps) => {
  const dispatch: AppDispatch = useDispatch()
  const theme = useTheme()

  // Use props if provided, otherwise fall back to defaults
  const [fireWatch, setFireWatch] = useState<FireWatch>(initialFireWatch ?? getBlankFireWatch())
  const [activeStep, setActiveStep] = useState<number>(initialActiveStep ?? 0)

  const { fireWatchSubmitting } = useSelector(fireWatchState)
  const { loading: updateLoading } = useSelector((state: RootState) => state.burnForecasts)

  const isLoading = fireWatchSubmitting || updateLoading

  const formRef = useRef<HTMLFormElement>(null)

  const steps: { key: string; label: string; component?: () => React.ReactNode }[] = [
    {
      key: 'info',
      label: 'Info'
    },
    {
      key: 'location',
      label: 'Location'
    },
    {
      key: 'weather-parameters',
      label: 'Weather'
    },
    {
      key: 'fuel-moisture-codes',
      label: 'Fuel Info'
    },
    {
      key: 'fire-behaviour-indices',
      label: 'FBP Indices'
    },
    {
      key: 'review-submit',
      label: 'Submit'
    }
  ]

  const handleBack = () => {
    setActiveStep(prevActiveStep => prevActiveStep - 1)
  }

  const handleNext = (event: React.FormEvent) => {
    event.preventDefault()
    if (formRef.current && !formRef.current.reportValidity()) {
      // if invalid, don't go to the next step
      return
    }
    if (activeStep === steps.length - 1) {
      handleSubmit()
    }
    setActiveStep(prevActiveStep => prevActiveStep + 1)
  }

  const handleStepLabelClick = (idx: number) => {
    if (!isEditMode) return
    if (isLoading || idx === activeStep) return

    if (formRef.current && !formRef.current.reportValidity()) {
      // invalid form, do not proceed
      return
    }
    setActiveStep(idx)
  }

  const handleReset = () => {
    setFireWatch(getBlankFireWatch())
    setActiveStep(0)
  }

  const handleSubmit = async () => {
    if (isNaN(fireWatch.id)) {
      dispatch(submitNewFireWatch(fireWatch))
    } else {
      dispatch(updateFireWatch(fireWatch))
    }
  }

  useEffect(() => {
    dispatch(fetchWxStations(getStations, StationSource.wildfire_one))
    dispatch(fetchFireWatchFireCentres())
  }, [])

  const isEditMode = !isNaN(fireWatch.id)

  return (
    <Box id="fire-watch-dashboard" sx={{ flexGrow: 1, width: `${FORM_MAX_WIDTH}px` }}>
      <Typography variant="h5" sx={{ padding: theme.spacing(2) }}>
        Burn Entry Form
      </Typography>
      <Stepper activeStep={activeStep} alternativeLabel sx={{ width: `${FORM_MAX_WIDTH}px` }}>
        {steps.map((step, idx) => (
          <Step key={step.key}>
            <StepLabel
              onClick={() => handleStepLabelClick(idx)}
              sx={
                isEditMode
                  ? {
                      cursor: 'pointer',
                      '&.Mui-disabled': {
                        cursor: 'pointer'
                      }
                    }
                  : undefined
              }
            >
              {step.label}
            </StepLabel>
          </Step>
        ))}
      </Stepper>
      <Box component="form" ref={formRef} onSubmit={handleNext}>
        {activeStep === 0 && <InfoStep fireWatch={fireWatch} setFireWatch={setFireWatch} />}
        {activeStep === 1 && <LocationStep fireWatch={fireWatch} setFireWatch={setFireWatch} />}
        {activeStep === 2 && <WeatherParametersStep fireWatch={fireWatch} setFireWatch={setFireWatch} />}
        {activeStep === 3 && <FuelStep fireWatch={fireWatch} setFireWatch={setFireWatch} />}
        {activeStep === 4 && <FireBehvaiourIndicesStep fireWatch={fireWatch} setFireWatch={setFireWatch} />}
        {activeStep === 5 && <ReviewSubmitStep fireWatch={fireWatch} setActiveStep={setActiveStep} />}
        {activeStep === 6 && <CompleteStep isEditMode={isEditMode} isLoading={isLoading} />}
        {activeStep < steps.length && (
          <Box sx={{ display: 'flex', flexDirection: 'row', pr: theme.spacing(4), width: `${FORM_MAX_WIDTH}px` }}>
            <Box sx={{ display: 'flex', flexGrow: 1, pl: theme.spacing(4) }}>
              <Button disabled={activeStep === 0 || isLoading} onClick={handleBack} variant="outlined" type="button">
                Back
              </Button>
            </Box>
            {isEditMode && (
              <Button onClick={onCloseModal} variant="outlined" disabled={isLoading} sx={{ mr: 2 }}>
                Cancel
              </Button>
            )}
            <Button variant="contained" type="submit" disabled={isLoading}>
              {activeStep === steps.length - 1 ? 'Submit' : 'Next'}
            </Button>
          </Box>
        )}
      </Box>
      {activeStep === steps.length && (
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'row',
            justifyContent: 'flex-end',
            pr: theme.spacing(4),
            width: `${FORM_MAX_WIDTH}px`
          }}
        >
          <Box sx={{ display: 'flex', flexGrow: 1, pl: theme.spacing(4) }}>
            <Button disabled={activeStep === 0 || isLoading} onClick={handleBack} variant="outlined">
              Back
            </Button>
          </Box>
          {isEditMode ? (
            <Button onClick={onCloseModal} variant="contained" disabled={isLoading}>
              Close
            </Button>
          ) : (
            <Button onClick={handleReset} variant="contained" disabled={isLoading}>
              Reset
            </Button>
          )}
        </Box>
      )}
    </Box>
  )
}

export default CreateFireWatch
