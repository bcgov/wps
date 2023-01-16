import React from 'react'
import Typography from '@mui/material/Typography'
import makeStyles from '@mui/styles/makeStyles'

interface SubheadingProps {
  title: string
}

const useStyles = makeStyles(theme => ({
  root: {
    backgroundColor: theme.palette.primary.main,
    color: theme.palette.primary.contrastText,
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    borderTop: '2px',
    borderColor: theme.palette.secondary.main,
    borderTopStyle: 'solid',
    height: '75px',
    [theme.breakpoints.down('sm')]: {
      height: '56px'
    }
  },
  text: {
    fontSize: '1.25rem',
    fontWeight: 700,
    paddingLeft: theme.spacing(1.25),
    [theme.breakpoints.down('sm')]: {
      fontSize: '1rem'
    }
  }
}))

const Subheading: React.FunctionComponent<SubheadingProps> = (props: SubheadingProps) => {
  const classes = useStyles()

  return (
    <div id="sidebar-header" className={classes.root}>
      <Typography className={classes.text}>{props.title}</Typography>
    </div>
  )
}

export default React.memo(Subheading)
