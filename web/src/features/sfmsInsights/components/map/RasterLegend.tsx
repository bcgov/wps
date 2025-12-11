import { Box, Typography } from '@mui/material'
import { ColorBreak } from './rasterColorBreaks'

interface RasterLegendProps {
  title: string
  colorBreaks: ColorBreak[]
}

const RasterLegend = ({ title, colorBreaks }: RasterLegendProps) => {
  return (
    <Box
      sx={{
        position: 'absolute',
        bottom: 20,
        right: 20,
        bgcolor: 'rgba(255, 255, 255, 0.95)',
        padding: '12px',
        borderRadius: '4px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
        zIndex: 1000,
        minWidth: '120px'
      }}
    >
      <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 1, fontSize: '13px' }}>
        {title}
      </Typography>
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
        {colorBreaks.map((colorBreak, index) => (
          <Box
            key={index}
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}
          >
            <Box
              sx={{
                width: '30px',
                height: '16px',
                bgcolor: colorBreak.color,
                border: '1px solid rgba(0,0,0,0.2)',
                flexShrink: 0
              }}
            />
            <Typography variant="caption" sx={{ fontSize: '11px' }}>
              {colorBreak.label}
            </Typography>
          </Box>
        ))}
      </Box>
    </Box>
  )
}

export default RasterLegend
