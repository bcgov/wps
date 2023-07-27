import React from 'react'
import { styled } from '@mui/material/styles'
import { Button } from '@mui/material'
const PREFIX = 'PercentileActionButtons'

const classes = {
  root: `${PREFIX}-root`,
  calculateBtn: `${PREFIX}-calculateBtn`
}

const Root = styled('div')({
  [`&.${classes.root}`]: {
    marginTop: 15
  },
  [`& .${classes.calculateBtn}`]: {
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
  return (
    <Root className={classes.root}>
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
    </Root>
  )
}
