import React from 'react'
import { Button } from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'

const useStyles = makeStyles({
  root: {
    marginTop: 15
  },
  fetchBtn: {
    marginLeft: 15
  }
})

interface Props {
  fetchDisabled: boolean
  onFetchClick: () => void
}

export const ActionButton: React.FunctionComponent<Props> = ({
  fetchDisabled,
  onFetchClick
}: Props) => {
  const classes = useStyles()

  return (
    <div className={classes.root}>
      <Button
        className={classes.fetchBtn}
        data-testid="calculate-percentiles-button"
        id="calculate-percentiles-button"
        disabled={fetchDisabled}
        variant="contained"
        color="primary"
        onClick={onFetchClick}
      >
        Fetch Data
      </Button>
    </div>
  )
}
