import React from 'react'
import makeStyles from '@mui/styles/makeStyles'
import { theme } from 'app/theme'
import { FOOTER_HEIGHT } from 'utils/constants'

const useStyles = makeStyles(() => ({
  root: {
    backgroundColor: theme.palette.primary.light,
    height: `${FOOTER_HEIGHT}px`
  }
}))

const Footer: React.FunctionComponent = () => {
  const classes = useStyles()

  return <div className={classes.root}></div>
}

export default React.memo(Footer)
