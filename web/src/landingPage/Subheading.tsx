import React from 'react'
import makeStyles from '@mui/styles/makeStyles'
import { theme } from 'app/theme'

interface SubheadingProps {
  title: string
}

const useStyles = makeStyles(() => ({
  root: {
    backgroundColor: theme.palette.primary.main,
    color: theme.palette.primary.contrastText,
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    borderTop: '2px',
    borderColor: theme.palette.secondary.main,
    borderTopStyle: 'solid',
    minHeight: '75px'
  },
  text: {
    fontSize: '21.6px',
    fontWeight: 700,
    paddingLeft: '10px'
  }
}))

const Subheading: React.FunctionComponent<SubheadingProps> = (props: SubheadingProps) => {
  const classes = useStyles()

  return (
    <React.Fragment>
      <div id="sidebar-header" className={classes.root}>
        <div className={classes.text}>{props.title}</div>
      </div>
    </React.Fragment>
  )
}

export default React.memo(Subheading)
