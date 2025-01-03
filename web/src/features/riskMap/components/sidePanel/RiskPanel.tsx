import React from 'react'
import { Box } from '@mui/material'

interface RiskPanelProps {
  children: React.ReactNode
}

const RiskPanel = React.forwardRef(({ children }: RiskPanelProps, ref: React.ForwardedRef<HTMLDivElement>) => {
  return (
    <Box data-testid="info-panel" ref={ref} sx={{ width: '550px', overflow: 'auto' }}>
      {children}
    </Box>
  )
})

RiskPanel.displayName = 'RiskPanel'

export default RiskPanel
