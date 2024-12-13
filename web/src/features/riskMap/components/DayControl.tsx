import React, { useState, useEffect } from 'react'
import { Box, Button, IconButton, Typography, Slider } from '@mui/material'
import PlayArrowIcon from '@mui/icons-material/PlayArrow'
import PauseIcon from '@mui/icons-material/Pause'
import { useDispatch, useSelector } from 'react-redux'
import { selectFireGrowthDay } from '@/app/rootReducer'
import { AppDispatch } from '@/app/store'
import { incrementDay, resetDay, setDay } from '@/features/riskMap/slices/fireGrowthSlice'

const DayControl: React.FC = () => {
  const { day } = useSelector(selectFireGrowthDay)
  const [playing, setPlaying] = useState<boolean>(false) // Play/pause state
  const dispatch: AppDispatch = useDispatch()

  useEffect(() => {
    let timer: NodeJS.Timeout | undefined

    if (playing) {
      timer = setInterval(() => {
        if (day === 3) {
          clearInterval(timer) // Clear interval at end
        } else {
          dispatch(incrementDay())
        }
      }, 1000) // Change day every second (adjust as needed)
    } else if (timer) {
      clearInterval(timer) // Clear interval when paused
    }

    return () => clearInterval(timer) // Cleanup on unmount or pause
  }, [playing])

  const handlePlayPause = () => {
    setPlaying(!playing) // Toggle play/pause state
  }

  const handleDayChange = (event: Event, newValue: number | number[]) => {
    dispatch(setDay(newValue as number)) // Update day manually with the slider
  }

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
      {/* Play/Pause Button */}
      <IconButton onClick={handlePlayPause} color="primary">
        {playing ? <PauseIcon /> : <PlayArrowIcon />}
      </IconButton>

      {/* Day Display */}
      <Typography variant="h6">Day: {day}</Typography>

      {/* Slider for manually changing days */}
      <Slider value={day} onChange={handleDayChange} min={1} max={4} aria-labelledby="day-slider" sx={{ width: 200 }} />

      {/* Manual Button to reset to Day 1 */}
      <Button onClick={() => dispatch(resetDay())} variant="outlined">
        Reset
      </Button>
    </Box>
  )
}

export default DayControl
