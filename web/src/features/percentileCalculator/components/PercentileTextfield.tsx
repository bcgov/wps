import React from 'react'
import { styled } from '@mui/material/styles'
import { TextField } from '@mui/material'
const PREFIX = 'PercentileTextfield'

const classes = {
  root: `${PREFIX}-root`
}

const StyledTextField = styled(TextField)({
  [`& .${classes.root}`]: {
    marginTop: 15,
    width: 300
  }
})

export const PercentileTextfield: React.FunctionComponent = () => {
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
