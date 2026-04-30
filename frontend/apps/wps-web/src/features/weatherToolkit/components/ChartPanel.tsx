import { Fullscreen, FullscreenExit } from '@mui/icons-material'
import { Box, CircularProgress, IconButton, Typography, useTheme } from '@mui/material'

interface ChartPanelProps {
  imageSrc: string | null
  chartKey: string
  isFailed: boolean
  isExpanded: boolean
  onToggleExpand: () => void
}

const ChartPanel = ({ imageSrc, chartKey, isFailed, isExpanded, onToggleExpand }: ChartPanelProps) => {
  const theme = useTheme()
  return (
    <Box sx={{ flexGrow: 1, overflow: 'hidden', bgcolor: '#B9B9B9', position: 'relative' }}>
      {imageSrc && !isFailed && (
        <img
          src={imageSrc}
          alt="4-panel chart"
          style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', objectFit: 'contain' }}
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
