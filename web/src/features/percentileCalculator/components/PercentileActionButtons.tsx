import React from 'react'
import { Button } from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'

const useStyles = makeStyles({
  root: {
    marginTop: 15
  },
  calculateBtn: {
    marginLeft: 15
  }
})

interface Props {
  calcDisabled: boolean
  onCalculateClick: () => void
  onResetClick: () => void
}

export const PercentileActionButtons: React.FunctionComponent<Props> = ({
  calcDisabled,
  onCalculateClick,
  onResetClick
}: Props) => {
  const classes = useStyles()

  return (
    <div className={classes.root}>
      <Button
        variant="contained"
        onClick={onResetClick}
        data-testid="reset-percentiles-button"
        id="reset-percentiles-button"
      >
        Reset
      </Button>

      <Button
        className={classes.calculateBtn}
        data-testid="calculate-percentiles-button"
        id="calculate-percentiles-button"
        disabled={calcDisabled}
        variant="contained"
        color="primary"
        onClick={onCalculateClick}
      >
        Calculate
      </Button>
    </div>
  )
}
