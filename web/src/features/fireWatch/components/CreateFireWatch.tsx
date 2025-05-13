import FuelStep from "@/features/fireWatch/components/steps/FuelStep"
import InfoStep from "@/features/fireWatch/components/steps/InfoStep"
import WeatherParametersStep from "@/features/fireWatch/components/steps/WeatherParametersStep"
import { FireWatch } from '@/features/fireWatch/interfaces'
import { getBlankFireWatch } from "@/features/fireWatch/utils"
import { Box, Button, Step, StepLabel, Stepper, Typography, useTheme } from "@mui/material"
import { useEffect, useState } from 'react'
import FireBehvaiourIndicesStep from '@/features/fireWatch/components/steps/FireBehviorIndicesStep'
import ReviewSubmitStep from '@/features/fireWatch/components/steps/ReviewSubmitStep'
import CompleteStep from '@/features/fireWatch/components/steps/CompleteStep'
import { useDispatch } from 'react-redux'
import { submitNewFireWatch } from '@/features/fireWatch/slices/fireWatchSlice'
import { AppDispatch } from '@/app/store'
import { fetchWxStations } from 'features/stations/slices/stationsSlice'
import { getStations, StationSource } from '@/api/stationAPI'
import LocationStep from '@/features/fireWatch/components/steps/LocationStep'
import { fetchFireWatchFireCentres } from 'features/fireWatch/slices/fireWatchFireCentresSlice'

export const FORM_MAX_WIDTH = 768

const CreateFireWatch = () => {
  const dispatch: AppDispatch = useDispatch()
  const theme = useTheme()
  const [activeStep, setActiveStep] = useState<number>(0)
  const [fireWatch, setFireWatch] = useState<FireWatch>(getBlankFireWatch())

  const steps: { key: string; label: string; component?: () => React.ReactNode }[] = [
    {
      key: 'info',
      label: 'Location & Basics'
    },
    {
      key: 'location',
      label: 'Burn Location'
    },
    {
      key: 'weather-parameters',
      label: 'Weather Parameters'
    },
    {
      key: 'fuel-moisture-codes',
      label: 'Fuel Type & Fuel Moisture Codes'
    },
    {
      key: 'fire-behaviour-indices',
      label: 'Fire Behaviour Indices'
    },
    {
      key: 'review-submit',
      label: 'Review and Submit'
    }
  ]

  const handleBack = () => {
    setActiveStep(prevActiveStep => prevActiveStep - 1)
  }

  const handleNext = () => {
    if (activeStep === steps.length - 1) {
      handleSubmit()
    }
    setActiveStep(prevActiveStep => prevActiveStep + 1)
  }

  const handleReset = () => {
    setFireWatch(getBlankFireWatch())
    setActiveStep(0)
  }

  const handleSubmit = () => {
    dispatch(submitNewFireWatch(fireWatch))
  }

  useEffect(() => {
    dispatch(fetchWxStations(getStations, StationSource.wildfire_one))
    dispatch(fetchFireWatchFireCentres())
  }, [])

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
              <StepLabel>{''}</StepLabel>
            </Step>
          )
        })}
      </Stepper>
      {activeStep === 0 && <InfoStep fireWatch={fireWatch} setFireWatch={setFireWatch} />}
      {activeStep === 1 && <LocationStep fireWatch={fireWatch} setFireWatch={setFireWatch} />}
      {activeStep === 2 && <WeatherParametersStep fireWatch={fireWatch} setFireWatch={setFireWatch} />}
      {activeStep === 3 && <FuelStep fireWatch={fireWatch} setFireWatch={setFireWatch} />}
      {activeStep === 4 && <FireBehvaiourIndicesStep fireWatch={fireWatch} setFireWatch={setFireWatch} />}
      {activeStep === 5 && <ReviewSubmitStep fireWatch={fireWatch} setActiveStep={setActiveStep} />}
      {activeStep === 6 && <CompleteStep />}
      {activeStep < steps.length && (
        <Box sx={{ display: 'flex', flexDirection: 'row', pr: theme.spacing(4), width: `${FORM_MAX_WIDTH}px` }}>
          <Box sx={{ display: 'flex', flexGrow: 1, pl: theme.spacing(4) }}>
            <Button disabled={activeStep === 0} onClick={handleBack} variant="outlined">
              Back
            </Button>
          </Box>
          <Button onClick={handleNext} variant="contained">
            {activeStep === steps.length - 1 ? 'Submit' : 'Next'}
          </Button>
        </Box>
      )}
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
          <Button onClick={handleReset} variant="contained">
            Reset
          </Button>
        </Box>
      )}
    </Box>
  )
}

export default CreateFireWatch