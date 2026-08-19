import { Fullscreen, FullscreenExit } from '@mui/icons-material'
import { Box, ButtonBase, CircularProgress, IconButton, Typography, useTheme } from '@mui/material'
import { useEffect, useState } from 'react'

// The four plots tile the generated image edge to edge in a 2x2 grid
// (see apply_4panel_frames in wps-weather), so each plot maps exactly to
// one quadrant of the image.
export enum PanelQuadrant {
  TOP_LEFT = 'topLeft',
  TOP_RIGHT = 'topRight',
  BOTTOM_LEFT = 'bottomLeft',
  BOTTOM_RIGHT = 'bottomRight'
}

export const panelRegistry: Record<PanelQuadrant, { label: string; row: 0 | 1; col: 0 | 1 }> = {
  [PanelQuadrant.TOP_LEFT]: { label: '500 hPa Height + Abs Vorticity', row: 0, col: 0 },
  [PanelQuadrant.TOP_RIGHT]: { label: 'MSLP + 1000-500 Thickness', row: 0, col: 1 },
  [PanelQuadrant.BOTTOM_LEFT]: { label: '700 hPa Height + 850-500 Relative Humidity', row: 1, col: 0 },
  [PanelQuadrant.BOTTOM_RIGHT]: { label: 'Precipitation', row: 1, col: 1 }
}

interface ChartPanelProps {
  imageSrc: string | null
  chartKey: string
  isFailed: boolean
  isExpanded: boolean
  onToggleExpand: () => void
}

const ChartPanel = ({ imageSrc, chartKey, isFailed, isExpanded, onToggleExpand }: ChartPanelProps) => {
  const theme = useTheme()
  const [focusedPanel, setFocusedPanel] = useState<PanelQuadrant | null>(null)

  useEffect(() => {
    if (!focusedPanel) return
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setFocusedPanel(null)
      }
    }
    globalThis.addEventListener('keydown', handleKeyDown)
    return () => globalThis.removeEventListener('keydown', handleKeyDown)
  }, [focusedPanel])

  const focused = focusedPanel ? panelRegistry[focusedPanel] : null

  return (
    <Box sx={{ flexGrow: 1, overflow: 'hidden', bgcolor: '#B9B9B9', position: 'relative' }}>
      {imageSrc && !isFailed && (
        <img
          src={imageSrc}
          alt={focused ? `${focused.label} panel` : '4-panel chart'}
          style={
            focused
              ? {
                  position: 'absolute',
                  top: focused.row === 0 ? 0 : '-100%',
                  left: focused.col === 0 ? 0 : '-100%',
                  width: '200%',
                  height: '200%',
                  objectFit: 'contain'
                }
              : { position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', objectFit: 'contain' }
          }
        />
      )}
      {imageSrc && !isFailed && !focusedPanel && (
        <Box
          sx={{
            position: 'absolute',
            inset: 0,
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gridTemplateRows: '1fr 1fr'
          }}
        >
          {Object.values(PanelQuadrant).map(quadrant => (
            <ButtonBase
              key={quadrant}
              onClick={() => setFocusedPanel(quadrant)}
              aria-label={`View ${panelRegistry[quadrant].label} panel full screen`}
              sx={{ '&:hover': { outline: '2px solid rgba(255,255,255,0.7)', outlineOffset: '-2px' } }}
            />
          ))}
        </Box>
      )}
      {imageSrc && !isFailed && focusedPanel && (
        <ButtonBase
          onClick={() => setFocusedPanel(null)}
          aria-label="Return to 4-panel view"
          sx={{ position: 'absolute', inset: 0 }}
        />
      )}
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
