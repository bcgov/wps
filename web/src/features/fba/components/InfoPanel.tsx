import React from 'react'
import { Grid } from '@mui/material'

interface InfoPanelProps {
  children: React.ReactNode
}

const InfoPanel = ({ children }: InfoPanelProps) => {
  return <Grid sx={{ maxWidth: 400, minWidth: 400 }}>{children}</Grid>
}

export default InfoPanel
