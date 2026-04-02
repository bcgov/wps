import React, { useMemo } from 'react'
import { IconButton, Slider, Paper, Box } from '@mui/material'
import { FirstPage, LastPage } from '@mui/icons-material'

interface TimelineControllerProps {
  currentHour: number
  setCurrentHour: React.Dispatch<React.SetStateAction<number>>
  start: number
  end: number
  step: number
}

interface SliderMark {
  label: string | undefined
  value: number
}

const TimelineController = ({ currentHour, setCurrentHour, start, end, step }: TimelineControllerProps) => {
  const handleSliderChange = (event: Event, newValue: number | number[]) => {
    if (Array.isArray(newValue)) {
      throw new TypeError('Slider value cannot be an array.')
    }
    setCurrentHour(newValue)
  }

  const handlePrev = () => {
    setCurrentHour(prev => Math.max(prev - step, 0))
  }

  const handleNext = () => {
    setCurrentHour(prev => Math.min(prev + 3, end))
  }

  const marks = useMemo(() => {
    const result: SliderMark[] = []
    for (let i = start; i <= end; i += step) {
      let label: string | undefined = undefined
      if (i === 0) {
        label = '0h'
      } else {
        label = i % 4 === 0 ? `+${i}h` : undefined
      }
      result.push({
        label,
        value: i
      })
    }
    return result
  }, [start, end, step])

  return (
    <Paper
      component="div"
      elevation={6}
      square
      sx={{
        height: 104,
        display: 'flex',
        alignItems: 'center',
        px: 5,
        gap: 6,
        zIndex: 30,
        bgcolor: '#fcfdfe',
        borderTop: '1px solid',
        borderColor: 'rgba(0,0,0,0.06)',
        boxShadow: '0 -4px 24px rgba(0,0,0,0.03)'
      }}
    >
      {/* VCR Controls */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <IconButton
          size="large"
          onClick={handlePrev}
          disabled={currentHour === 0}
          aria-label="Previous timestep"
          sx={{
            width: 44,
            height: 44,
            border: '1px solid',
            borderColor: 'rgba(0,51,102,0.15)',
            bgcolor: 'white',
            transition: 'all 0.2s',
            '&:hover:not(:disabled)': { bgcolor: '#f0f4f8', borderColor: '#003366', transform: 'scale(1.05)' },
            '&:disabled': { opacity: 0.5, borderColor: 'rgba(0,0,0,0.1)' },
            boxShadow: '0 2px 8px rgba(0,0,0,0.05)'
          }}
        >
          <FirstPage color="primary" />
        </IconButton>

        <IconButton
          size="large"
          onClick={handleNext}
          disabled={currentHour >= end}
          aria-label="Next timestep"
          sx={{
            width: 44,
            height: 44,
            border: '1px solid',
            borderColor: 'rgba(0,51,102,0.15)',
            bgcolor: 'white',
            transition: 'all 0.2s',
            '&:hover:not(:disabled)': { bgcolor: '#f0f4f8', borderColor: '#003366', transform: 'scale(1.05)' },
            '&:disabled': { opacity: 0.5, borderColor: 'rgba(0,0,0,0.1)' },
            boxShadow: '0 2px 8px rgba(0,0,0,0.05)'
          }}
        >
          <LastPage color="primary" />
        </IconButton>
      </Box>

      <Slider
        value={currentHour}
        onChange={handleSliderChange}
        step={3}
        marks={marks}
        min={0}
        max={end}
        valueLabelDisplay="auto"
        aria-label={`Timeline slider 0 to ${end} hours`}
        sx={{
          color: '#003366',
          height: 8,
          '& .MuiSlider-thumb': {
            width: 26,
            height: 26,
            backgroundColor: 'white',
            border: '4px solid #E3A82B',
            boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
            '&:hover, &.Mui-focusVisible, &.Mui-active': {
              boxShadow: '0px 0px 0px 8px rgba(227, 168, 43, 0.15)'
            }
          },
          '& .MuiSlider-rail': {
            backgroundColor: 'rgba(0,51,102,0.1)',
            opacity: 1,
            height: 8,
            borderRadius: 4
          },
          '& .MuiSlider-track': {
            height: 8,
            borderRadius: 4,
            background: 'linear-gradient(90deg, #003366 0%, #005599 100%)',
            border: 'none'
          },
          '& .MuiSlider-mark': {
            backgroundColor: 'rgba(0,51,102,0.3)',
            height: 12,
            width: 2,
            borderRadius: 1,
            '&.MuiSlider-markActive': {
              opacity: 1,
              backgroundColor: 'rgba(255,255,255,0.7)'
            }
          },
          '& .MuiSlider-markLabel': {
            fontSize: '0.7rem',
            fontWeight: 700,
            color: '#64748b',
            marginTop: '6px'
          }
        }}
      />
    </Paper>
  )
}

export default TimelineController
