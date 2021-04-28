import React from 'react'
import { Card, CardContent, Typography } from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'
import PictureAsPdfIcon from '@material-ui/icons/PictureAsPdf'

import PDF from 'documents/90th_percentile_calculator_rationale.pdf'

const useStyles = makeStyles({
  cardContent: {
    maxWidth: 800,
  },
  body2: {
    marginBottom: 8,
  },
  pdfLink: {
    display: 'flex',
  },
  pdfIcon: {
    marginLeft: 2,
  },
})

export const PercentileCalcDocumentation: React.FunctionComponent = () => {
  const classes = useStyles()

  return (
    <Card data-testid="percentile-documentation-card">
      <CardContent className={classes.cardContent}>
        <Typography variant="h6">How Are These Values Calculated?</Typography>
        <Typography className={classes.body2} variant="body2">
          Daily weather data (collected at noon local time) for the core fire seasons in
          the selected time range is collected for each of the selected weather stations.
        </Typography>
        <Typography className={classes.body2} variant="body2">
          The value reported for each of the FFMC, BUI, and ISI indexes represents the 90
          <sup>th</sup> percentile of those index values for each individual weather
          station over the time range. When more than one weather station is selected, the
          mean for the indexes of each 90
          <sup>th</sup> percentile is also calculated.
        </Typography>
        <Typography className={classes.body2} variant="body2">
          For example, when looking at a weather station over 10 years for a 4-month long
          core fire season, the 90<sup>th</sup> percentile indicates the 1080<sup>th</sup>{' '}
          largest value for each daily index value at the weather station (30 days * 4
          months * 10 years * 0.9 = 1080).
        </Typography>
        <Typography className={classes.body2} variant="body2">
          <a
            className={classes.pdfLink}
            href={PDF}
            target="_blank"
            rel="noopener noreferrer"
          >
            Rationale for the development of Core Wildfire Seasons
            <PictureAsPdfIcon className={classes.pdfIcon} fontSize="small" />
          </a>
        </Typography>
      </CardContent>
    </Card>
  )
}
