import { Box } from '@mui/material'

interface RasterTooltipProps {
  label: string
  value: number | string | null
  pixelCoords: [number, number] | null
  decimalPlaces?: number
  snowCovered?: boolean
}

const RasterTooltip = ({ label, value, pixelCoords, decimalPlaces = 0, snowCovered = false }: RasterTooltipProps) => {
  if (value === null || !pixelCoords) {
    return null
  }

  const displayValue = typeof value === 'number' ? value.toFixed(decimalPlaces) : value
  const tooltipText = label ? `${label}: ${displayValue}` : displayValue

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
        display: 'flex',
        alignItems: 'center',
        gap: '6px',
        pointerEvents: 'none',
        zIndex: 1000
      }}
    >
      {snowCovered && (
        <Box
          component="span"
          role="img"
          aria-label="Snow cover"
          sx={{
            width: '20px',
            height: '20px',
            flexShrink: 0,
            bgcolor: '#b3e5fc',
            mask: 'url(/images/snowflake.svg) center / contain no-repeat',
            WebkitMask: 'url(/images/snowflake.svg) center / contain no-repeat'
          }}
        />
      )}
      {tooltipText}
    </Box>
  )
}

export default RasterTooltip
