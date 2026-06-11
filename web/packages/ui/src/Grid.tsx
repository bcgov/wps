import { Grid, type GridProps } from '@mui/material'
import type React from 'react'

export const GridContainer: React.FunctionComponent<GridProps> = (props: GridProps) => (
  <Grid container spacing={2} {...props} />
)

export const GridItem: React.FunctionComponent<GridProps> = (props: GridProps) => (
  <Grid size={{ lg: 4, md: 6, sm: 12, xs: 12 }} {...props} />
)
