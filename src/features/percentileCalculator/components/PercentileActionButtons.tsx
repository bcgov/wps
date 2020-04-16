import React from 'react'
import { Button } from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'

import { Station } from 'api/stationAPI'

const useStyles = makeStyles({
  root: {
    marginTop: 15
  },
  calculateBtn: {
    marginLeft: 15
  }
})

interface Props {
  stations: Station[]
  onCalculateClick: () => void
  onResetClick: () => void
}

export const PercentileActionButtons = ({
  stations,
  onCalculateClick,
  onResetClick
}: Props) => {
  const classes = useStyles()

  return (
    <div className={classes.root}>
      <Button variant="contained" onClick={onResetClick}>
        Reset
      </Button>

      <Button
        className={classes.calculateBtn}
        data-testid="calculate-percentiles-button"
        disabled={stations.length === 0}
        variant="contained"
        color="primary"
        onClick={onCalculateClick}
      >
        Calculate
      </Button>
    </div>
  )
}
