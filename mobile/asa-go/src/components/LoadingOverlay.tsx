import { Box, CircularProgress, Typography } from '@mui/material'
import { useEffect, useRef, useState } from 'react'

const SHOW_DELAY_MS = 200
const MINIMUM_VISIBLE_MS = 400

interface LoadingOverlayProps {
  loading: boolean
}

const LoadingOverlay = ({ loading }: LoadingOverlayProps) => {
  const [visible, setVisible] = useState(false)
  const visibleSinceRef = useRef<number | null>(null)

  useEffect(() => {
    if (loading && !visible) {
      const showTimer = window.setTimeout(() => {
        visibleSinceRef.current = Date.now()
        setVisible(true)
      }, SHOW_DELAY_MS)

      return () => window.clearTimeout(showTimer)
    }

    if (!loading && visible) {
      const elapsed = Date.now() - (visibleSinceRef.current ?? Date.now())
      const hideTimer = window.setTimeout(
        () => {
          visibleSinceRef.current = null
          setVisible(false)
        },
        Math.max(0, MINIMUM_VISIBLE_MS - elapsed)
      )

      return () => window.clearTimeout(hideTimer)
    }
  }, [loading, visible])

  if (!visible) return null

  return (
    <Box
      data-testid="loading-overlay"
      role="status"
      aria-live="polite"
      sx={{
        alignItems: 'center',
        backgroundColor: 'rgba(255, 255, 255, 0.85)',
        display: 'flex',
        flexDirection: 'column',
        inset: 0,
        justifyContent: 'center',
        position: 'absolute',
        zIndex: theme => theme.zIndex.modal + 1
      }}
    >
      <Typography color="primary" variant="h6" sx={{ mb: 2 }}>
        Data Updating
      </Typography>
      <CircularProgress aria-label="Data Updating" color="primary" />
    </Box>
  )
}

export default LoadingOverlay
