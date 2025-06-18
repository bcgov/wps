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
import { useDispatch } from 'react-redux'

export const FORM_MAX_WIDTH = 768

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
  const [locationError, setLocationError] = useState(false)

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
    if (activeStep === 1 && (!fireWatch.geometry || fireWatch.geometry.length === 0)) {
      setLocationError(true)
      return
    }
    if (formRef.current && !formRef.current.reportValidity()) {
      // if invalid, don't go to the next step
      return
    }
    if (activeStep === steps.length - 1) {
      handleSubmit()
    }
    setActiveStep(prevActiveStep => prevActiveStep + 1)
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
        {steps.map(step => {
          const stepProps: { completed?: boolean } = {}
          return (
            <Step key={step.key} {...stepProps}>
              <StepLabel>{step.label}</StepLabel>
            </Step>
          )
        })}
      </Stepper>
      <Box component="form" ref={formRef} onSubmit={handleNext}>
        {activeStep === 0 && <InfoStep fireWatch={fireWatch} setFireWatch={setFireWatch} />}
        {activeStep === 1 && (
          <LocationStep
            fireWatch={fireWatch}
            setFireWatch={setFireWatch}
            showLocationError={locationError}
            onCloseLocationError={() => setLocationError(false)}
          />
        )}
        {activeStep === 2 && <WeatherParametersStep fireWatch={fireWatch} setFireWatch={setFireWatch} />}
        {activeStep === 3 && <FuelStep fireWatch={fireWatch} setFireWatch={setFireWatch} />}
        {activeStep === 4 && <FireBehvaiourIndicesStep fireWatch={fireWatch} setFireWatch={setFireWatch} />}
        {activeStep === 5 && <ReviewSubmitStep fireWatch={fireWatch} setActiveStep={setActiveStep} />}
        {activeStep === 6 && <CompleteStep isEditMode={isEditMode} />}
        {activeStep < steps.length && (
          <Box sx={{ display: 'flex', flexDirection: 'row', pr: theme.spacing(4), width: `${FORM_MAX_WIDTH}px` }}>
            <Box sx={{ display: 'flex', flexGrow: 1, pl: theme.spacing(4) }}>
              <Button disabled={activeStep === 0} onClick={handleBack} variant="outlined" type="button">
                Back
              </Button>
            </Box>
            <Button variant="contained" type="submit">
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
            <Button disabled={activeStep === 0} onClick={handleBack} variant="outlined">
              Back
            </Button>
          </Box>
          {isEditMode ? (
            <Button onClick={onCloseModal} variant="contained">
              Close
            </Button>
          ) : (
            <Button onClick={handleReset} variant="contained">
              Reset
            </Button>
          )}
        </Box>
      )}
    </Box>
  )
}

export default CreateFireWatch
