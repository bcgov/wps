import React from 'react'
import { styled } from '@mui/material/styles'
const PREFIX = 'BetaTag'

const classes = {
  root: `${PREFIX}-root`
}

const Root = styled('span')(({ theme }) => ({
  [`&.${classes.root}`]: {
    backgroundColor: theme.palette.primary.main,
    borderRadius: '25px',
    color: theme.palette.primary.contrastText,
    fontSize: '1rem',
    paddingBottom: theme.spacing(0.5),
    paddingLeft: theme.spacing(1.25),
    paddingRight: theme.spacing(1.25),
    paddingTop: theme.spacing(0.5),
    marginLeft: theme.spacing(2)
  }
}))

const BetaTag: React.FunctionComponent = () => {
  return <Root className={classes.root}>Beta</Root>
}

export default React.memo(BetaTag)
