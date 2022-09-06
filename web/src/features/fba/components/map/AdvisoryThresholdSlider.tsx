import { Box, Grid, Input, Slider } from '@mui/material'
import React from 'react'

export interface AdvisoryThresholdSliderProps {
  testId?: string
  advisoryThreshold: number
  setAdvisoryThreshold: React.Dispatch<React.SetStateAction<number>>
}
const AdvisoryThresholdSlider = ({ advisoryThreshold, setAdvisoryThreshold }: AdvisoryThresholdSliderProps) => {
  const handleSliderChange = (event: Event, newValue: number | number[]) => {
    if (Array.isArray(newValue)) {
      setAdvisoryThreshold(newValue[0])
    } else {
      setAdvisoryThreshold(newValue)
    }
  }
  const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setAdvisoryThreshold(event.target.value === '' ? 0 : Number(event.target.value))
  }
  return (
    <Box sx={{ width: 250 }}>
      <Grid container spacing={2}>
        <Grid item xs>
          <Slider aria-label="Advisory Threshold Slider" value={advisoryThreshold} onChange={handleSliderChange} />
        </Grid>
        <Grid item>
          <Input
            value={advisoryThreshold}
            size="small"
            onChange={handleInputChange}
            inputProps={{
              step: 1,
              min: 0,
              max: 100,
              type: 'number',
              'aria-labelledby': 'input-slider'
            }}
          />
        </Grid>
      </Grid>
    </Box>
  )
}

export default React.memo(AdvisoryThresholdSlider)
