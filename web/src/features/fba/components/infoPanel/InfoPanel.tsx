import React from 'react'
import { Grid } from '@mui/material'

interface InfoPanelProps {
  children: React.ReactNode
}

// A component to host information in a side panel in ASA.
const InfoPanel = React.forwardRef(({ children }: InfoPanelProps, ref: React.ForwardedRef<HTMLDivElement>) => {
  return (
    <Grid data-testid="info-panel" item ref={ref} sx={{ width: '500px', overflowY: 'auto' }}>
      {children}
    </Grid>
  )
})

InfoPanel.displayName = 'InfoPanel'

export default InfoPanel
