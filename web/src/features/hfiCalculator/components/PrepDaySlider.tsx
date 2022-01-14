import { Slider, Typography } from '@material-ui/core'
import React, { useState } from 'react'

const MIN_PREP_DAYS = 2
const MAX_PREP_DAYS = 5

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

const PrepDaySlider = () => {
  const [days, setDays] = useState(MAX_PREP_DAYS)
  return (
    <React.Fragment>
      <Typography variant="button" gutterBottom>
        Number of Prep Days
      </Typography>
      <Slider
        aria-label="Prep Day Range"
        marks={PREP_DAY_RANGE_OPTIONS}
        max={MAX_PREP_DAYS}
        min={MIN_PREP_DAYS}
        onChange={(_, timeRange) => {
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

export default React.memo(PrepDaySlider)
