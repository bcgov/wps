import React from 'react'
import { Card, CardContent, Typography } from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'

const useStyles = makeStyles({
  cardContent: {
    maxWidth: 1000
  },
  body2: {
    marginBottom: 8
  },
  pdfLink: {
    display: 'flex'
  },
  pdfIcon: {
    marginLeft: 2
  }
})

export const PeakBurninessDocumentation: React.FunctionComponent = () => {
  const classes = useStyles()

  return (
    <Card data-testid="peak-burniness-documentation-card">
      <CardContent className={classes.cardContent}>
        <Typography variant="h6">How Are These Values Calculated?</Typography>
        <Typography className={classes.body2} variant="body2">
          Hourly weather data for April 1 - September 30 between years 2011-2020
          (inclusive), as reported by BC FireWeather Phase 1, were analyzed for each BC
          weather station.
        </Typography>
        <Typography className={classes.body2} variant="body2">
          For each weather station, the maximum temperature, wind speed, FFMC, and FWI,
          and the minimum relative humidity was calculated for each day in the time range.
          These daily extremes were then grouped into weeks for each weather station,
          generating a list of values. The values listed in the table represent the median
          value for each weather variable.
        </Typography>
      </CardContent>
    </Card>
  )
}
