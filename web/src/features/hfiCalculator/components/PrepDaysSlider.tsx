import { Slider, Typography } from '@material-ui/core'
import React from 'react'

export const MIN_PREP_DAYS = 2
export const MAX_PREP_DAYS = 5

const PREP_DAY_RANGE_OPTIONS = [
  {
    value: MIN_PREP_DAYS,
    label: MIN_PREP_DAYS
  },
  {
    value: 3,
    label: 3
  },
  {
    value: 4,
    label: 4
  },
  {
    value: MAX_PREP_DAYS,
    label: MAX_PREP_DAYS
  }
]

export interface PrepDaySliderProps {
  days: number
  setDays: React.Dispatch<React.SetStateAction<number>>
}

const PrepDaysSlider = ({ days, setDays }: PrepDaySliderProps) => {
  return (
    <React.Fragment>
      <Typography variant="button" gutterBottom>
        Number of Prep Days
      </Typography>
      <Slider
        data-testid="prep-days-slider"
        aria-label="Prep Day Range"
        name="input-prep-days-input"
        marks={PREP_DAY_RANGE_OPTIONS}
        max={MAX_PREP_DAYS}
        min={MIN_PREP_DAYS}
        onChange={(_, timeRange) => {
          console.log('Been changed')
          if (typeof timeRange === 'number') {
            setDays(timeRange)
          }
        }}
        step={null}
        value={days}
      />
    </React.Fragment>
  )
}

export default React.memo(PrepDaysSlider)
