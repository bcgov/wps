import Slider from '@mui/material/Slider'
import Typography from '@mui/material/Typography'
import React from 'react'

interface DistanceSliderProps {
  spreadDistance: number
  setSpreadDistance: React.Dispatch<React.SetStateAction<number>>
}

const DistanceSlider = ({ spreadDistance, setSpreadDistance }: DistanceSliderProps) => {
  return (
    <>
      <Typography gutterBottom>Fire Spread Distance: {spreadDistance} m</Typography>
      <Slider
        value={spreadDistance}
        onChange={(event, newValue) => setSpreadDistance(newValue as number)}
        min={0}
        max={5000}
        step={10}
        valueLabelDisplay="auto"
      />
    </>
  )
}

export default DistanceSlider
