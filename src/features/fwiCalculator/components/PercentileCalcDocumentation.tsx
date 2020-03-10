import React from 'react'
import { Card, CardContent, Typography } from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'

const useStyles = makeStyles({
  title: {
    fontSize: 18,
    marginBottom: 10,
    color: '#000000'
  },
  cardContent: {
    maxWidth: 800
  },
  text: {
    color: '#333333',
    fontSize: 14,
    marginBottom: 10
  }
})

export const PercentileCalcDocumentation = () => {
  const classes = useStyles()

  return (
    <Card data-testid="percentile-documentation-card">
      <CardContent className={classes.cardContent}>
        <Typography className={classes.title}>
          How Are These Values Calculated?
        </Typography>
        <Typography className={classes.text}>
          Daily weather data (collected at noon local time) for the core fire
          seasons in the selected time range is collected for each of the
          selected weather stations.
        </Typography>
        <Typography className={classes.text}>
          The value reported for each of the FFMC, BUI, and ISI indexes
          represents the 90<sup>th</sup> percentile of those index values for
          each individual weather station over the time range. When more than
          one weather station is selected, the mean for the indexes of each 90
          <sup>th</sup> percentile is also calculated.
        </Typography>
        <Typography className={classes.text}>
          For example, when looking at a weather station over 10 years for a
          4-month long core fire season, the 90<sup>th</sup> percentile
          indicates the 1080<sup>th</sup> largest value for each daily index
          value at the weather station (30 days * 4 months * 10 years * 0.9 =
          1080).
        </Typography>
      </CardContent>
    </Card>
  )
}
