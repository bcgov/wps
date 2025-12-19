import { Box } from '@mui/material'

interface RasterTooltipProps {
  label: string
  value: number | string | null
  pixelCoords: [number, number] | null
}

const RasterTooltip = ({ label, value, pixelCoords }: RasterTooltipProps) => {
  if (value === null || !pixelCoords) {
    return null
  }

  return (
    <Box
      sx={{
        position: 'absolute',
        left: pixelCoords[0] + 15,
        top: pixelCoords[1] + 15,
        bgcolor: 'rgba(0, 0, 0, 0.8)',
        color: 'white',
        padding: '4px 8px',
        borderRadius: '4px',
        fontSize: '12px',
        pointerEvents: 'none',
        zIndex: 1000
      }}
    >
      {label}: {value}
    </Box>
  )
}

export default RasterTooltip
