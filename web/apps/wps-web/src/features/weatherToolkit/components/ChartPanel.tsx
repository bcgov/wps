import { Fullscreen, FullscreenExit, RestartAlt, ZoomIn, ZoomOut } from '@mui/icons-material'
import { Box, CircularProgress, IconButton, Typography, useTheme } from '@mui/material'
import { useState } from 'react'

interface ChartPanelProps {
  imageSrc: string | null
  chartKey: string
  isFailed: boolean
  isExpanded: boolean
  onToggleExpand: () => void
}

const ChartPanel = ({ imageSrc, chartKey, isFailed, isExpanded, onToggleExpand }: ChartPanelProps) => {
  const theme = useTheme()
  const [zoom, setZoom] = useState(1)
  const hasImage = Boolean(imageSrc) && !isFailed
  return (
    <Box sx={{ flexGrow: 1, minWidth: 0, minHeight: 0, overflow: 'hidden', bgcolor: '#B9B9B9', position: 'relative' }}>
      {imageSrc && !isFailed && (
        <Box
          role="region"
          aria-label="Chart viewport"
          tabIndex={0}
          onKeyDown={event => event.stopPropagation()}
          sx={{ position: 'absolute', inset: 0, overflow: 'auto' }}
        >
          <Box sx={{ width: `${zoom * 100}%`, height: `${zoom * 100}%`, position: 'relative' }}>
            <img
              src={imageSrc}
              alt="4-panel chart"
              draggable={false}
              style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', objectFit: 'contain' }}
            />
          </Box>
        </Box>
      )}
      <Box
        role="group"
        aria-label="Chart zoom controls"
        sx={{
          position: 'absolute',
          top: theme.spacing(1),
          left: theme.spacing(1),
          zIndex: 1,
          display: 'flex',
          alignItems: 'center',
          bgcolor: 'rgba(255,255,255,0.95)',
          borderRadius: 1
        }}
      >
        <IconButton
          aria-label="Zoom out"
          disabled={!hasImage || zoom <= 1}
          onClick={() => setZoom(prev => Math.max(1, prev - 0.5))}
        >
          <ZoomOut />
        </IconButton>
        <Typography aria-live="polite" sx={{ minWidth: 44, textAlign: 'center' }}>{`${zoom * 100}%`}</Typography>
        <IconButton
          aria-label="Zoom in"
          disabled={!hasImage || zoom >= 3}
          onClick={() => setZoom(prev => Math.min(3, prev + 0.5))}
        >
          <ZoomIn />
        </IconButton>
        <IconButton aria-label="Fit chart to view" disabled={!hasImage || zoom === 1} onClick={() => setZoom(1)}>
          <RestartAlt />
        </IconButton>
      </Box>
      {!imageSrc && !isFailed && (
        <Box sx={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <CircularProgress />
        </Box>
      )}
      <IconButton
        onClick={onToggleExpand}
        aria-label={isExpanded ? 'Restore header and footer' : 'Expand chart'}
        sx={{
          position: 'absolute',
          top: theme.spacing(1),
          right: theme.spacing(1),
          zIndex: 1,
          bgcolor: 'rgba(255,255,255,0.85)',
          '&:hover': { bgcolor: 'white' }
        }}
      >
        {isExpanded ? <FullscreenExit /> : <Fullscreen />}
      </IconButton>
      {isFailed && (
        <Box
          sx={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 1
          }}
        >
          <Typography variant="h6">Image not available</Typography>
          <Typography variant="body2" sx={{ wordBreak: 'break-all', px: 4, textAlign: 'center' }}>
            {chartKey}
          </Typography>
        </Box>
      )}
    </Box>
  )
}

export default ChartPanel
