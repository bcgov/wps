import { TextField } from '@mui/material'
import { styled } from '@mui/material/styles'
import type React from 'react'

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
    <StyledTextField
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
