import { Box } from '@mui/material'
import Slider from '@mui/material/Slider'
import Typography from '@mui/material/Typography'
import React from 'react'

interface DistanceSliderProps {
  spreadDistance: number
  setSpreadDistance: React.Dispatch<React.SetStateAction<number>>
}

const DistanceSlider = ({ spreadDistance, setSpreadDistance }: DistanceSliderProps) => {
  return (
    <Box
      sx={{
        marginLeft: '2rem',
        display: 'flex',
        flexDirection: 'column'
      }}
    >
      <Typography
        gutterBottom
        sx={{
          width: '250px',
          display: 'inline-block'
        }}
      >
        Fire Spread Distance: {spreadDistance} m
      </Typography>
      <Slider
        value={spreadDistance}
        onChange={(event, newValue) => setSpreadDistance(newValue as number)}
        min={100}
        max={10000}
        step={250}
        valueLabelDisplay="off"
        sx={{ width: '200px' }}
      />
    </Box>
  )
}

export default DistanceSlider
