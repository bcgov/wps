import React from 'react'
import makeStyles from '@mui/styles/makeStyles'

const useStyles = makeStyles(theme => ({
  root: {
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
  const classes = useStyles()
  return <span className={classes.root}>Beta</span>
}

export default React.memo(BetaTag)
