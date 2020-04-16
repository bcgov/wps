import React from 'react'
import { InputLabel, makeStyles } from '@material-ui/core'
import Slider from 'components/Slider'

const useStyles = makeStyles({
  root: {
    marginTop: 20
  },
  inputLabel: {
    marginBottom: 5
  }
})

interface Props {
  timeRange: number
  onYearRangeChange: (yearRangeNumber: number) => void
}

const MIN_YEARS = 0

const MAX_YEARS = new Date().getFullYear() - 1970

const TIME_RANGE_OPTIONS = [
  {
    value: MIN_YEARS,
    label: '0'
  },
  {
    value: 10,
    label: '10'
  },
  {
    value: 20,
    label: '20'
  },
  {
    value: MAX_YEARS,
    label: 'Full'
  }
]

export const TimeRangeSlider = (props: Props) => {
  const classes = useStyles()
  return (
    <div className={classes.root} data-testid="time-range-slider">
      <InputLabel className={classes.inputLabel}>Time Range (years)</InputLabel>
      <Slider
        aria-label="Time Range"
        marks={TIME_RANGE_OPTIONS}
        max={MAX_YEARS}
        min={MIN_YEARS}
        onChange={(_, timeRange) => {
          if (typeof timeRange === 'number') {
            if (timeRange === 0) return
            props.onYearRangeChange(timeRange)
          }
        }}
        step={null}
        value={props.timeRange}
      />
    </div>
  )
}
