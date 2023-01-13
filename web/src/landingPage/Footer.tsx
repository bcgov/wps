import React from 'react'
import { styled } from '@mui/material/styles'
import makeStyles from '@mui/styles/makeStyles'
import { Link } from 'react-router-dom'

const useStyles = makeStyles(theme => ({
  links: {
    display: 'flex',
    fontSize: '0.75rem',
    paddingBottom: theme.spacing(2),
    paddingLeft: theme.spacing(1),
    paddingTop: theme.spacing(2)
  },
  root: {
    backgroundColor: theme.palette.primary.main,
    minHeight: '80px'
  }
}))

const VerticalDivider: React.FunctionComponent = () => {
  return <div style={{ color: "#FFFFFF" }}>|</div>
}

const StyledLink = styled(Link)(
  ({theme}) => ({
    color: '#FFFFFF',
    paddingLeft: theme.spacing(1),
    paddingRight: theme.spacing(1),
    textDecoration: 'none'
  })
)

const Footer: React.FunctionComponent = () => {
  const classes = useStyles()

  return (
    <div className={classes.root}>
      <div className={classes.links}>
        <StyledLink to={{ pathname: '/' }}>Home</StyledLink>
        <VerticalDivider />
        <StyledLink to={{ pathname: '/' }}>Disclaimer</StyledLink>
        <VerticalDivider />
        <StyledLink to={{ pathname: '/' }}>Privacy</StyledLink>
        <VerticalDivider />
        <StyledLink to={{ pathname: '/' }}>Accessibility</StyledLink>
        <VerticalDivider />
        <StyledLink to={{ pathname: '/' }}>Copyright</StyledLink>
        <VerticalDivider />
        <StyledLink to={{ pathname: '/' }}>Contact Us</StyledLink>
      </div>
    </div>
  )
}

export default React.memo(Footer)
