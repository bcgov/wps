import React from 'react'
import { TextField } from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'

const useStyles = makeStyles({
  root: {
    width: 300
  }
})

export const PercentileTextfield = () => {
  const classes = useStyles()
  return (
    <TextField
      disabled
      data-testid="percentile-textfield"
      id="percentile-textfield"
      label="Percentile (%)"
      defaultValue="90"
      variant="outlined"
      className={classes.root}
      size="small"
    />
  )
}
