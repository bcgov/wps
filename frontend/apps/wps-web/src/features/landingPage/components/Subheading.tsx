import React from 'react'
import { styled } from '@mui/material/styles'
import Typography from '@mui/material/Typography'
const PREFIX = 'Subheading'

const classes = {
  root: `${PREFIX}-root`,
  text: `${PREFIX}-text`
}

const Root = styled('div')(({ theme }) => ({
  [`&.${classes.root}`]: {
    backgroundColor: theme.palette.primary.main,
    color: theme.palette.primary.contrastText,
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    borderTop: '2px',
    borderColor: theme.palette.secondary.main,
    borderTopStyle: 'solid',
    height: '56px'
  },

  [`& .${classes.text}`]: {
    fontSize: '1.25rem',
    fontWeight: 700,
    paddingLeft: theme.spacing(1.25),
    [theme.breakpoints.down('sm')]: {
      fontSize: '1rem'
    }
  }
}))

interface SubheadingProps {
  title: string
}

const Subheading: React.FunctionComponent<SubheadingProps> = (props: SubheadingProps) => {
  return (
    <Root id="sidebar-header" className={classes.root}>
      <Typography className={classes.text}>{props.title}</Typography>
    </Root>
  )
}

export default React.memo(Subheading)
