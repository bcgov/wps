import React from 'react'
import { styled } from '@mui/material/styles'
import { InputLabel, Slider } from '@mui/material'
const PREFIX = 'TimeRangeSlider'

const classes = {
  root: `${PREFIX}-root`,
  inputLabel: `${PREFIX}-inputLabel`,
  slider: `${PREFIX}-slider`
}

const Root = styled('div')({
  [`&.${classes.root}`]: {
    marginTop: 20
  },
  [`& .${classes.inputLabel}`]: {
    marginBottom: 5
  },
  [`& .${classes.slider}`]: {
    width: 300
  }
})

interface Props {
  timeRange: number
  onYearRangeChange: (yearRangeNumber: number) => void
}

export const earliestYearAvailableForCalculation = 1970
export const yearWhenTheCalculationIsDone = 2020

const MIN_YEARS = 0
const MAX_YEARS = yearWhenTheCalculationIsDone - earliestYearAvailableForCalculation

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

export const TimeRangeSlider: React.FunctionComponent<Props> = (props: Props) => {
  return (
    <Root className={classes.root} data-testid="time-range-slider">
      <InputLabel className={classes.inputLabel}>Time Range (years)</InputLabel>
      <Slider
        className={classes.slider}
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
    </Root>
  )
}
