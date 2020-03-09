import React from 'react'
import { Grid, GridProps } from '@material-ui/core'

export const GridContainer = (props: GridProps) => (
  <Grid container spacing={2} {...props} />
)

export const GridItem = (props: GridProps) => (
  <Grid item lg={4} md={6} sm={12} xs={12} {...props} />
)
