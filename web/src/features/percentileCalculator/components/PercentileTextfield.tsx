import React from 'react'
import { TextField } from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'

const useStyles = makeStyles({
  root: {
    marginTop: 15,
    width: 300
  }
})

export const PercentileTextfield: React.FunctionComponent = () => {
  const classes = useStyles()

  return (
    <TextField
      id="percentile-textfield"
      className={classes.root}
      data-testid="percentile-textfield"
      disabled
      label="Percentile (%)"
      defaultValue="90"
      variant="outlined"
      size="small"
    />
  )
}
