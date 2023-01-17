import React from 'react'
import { styled, useTheme } from '@mui/material/styles'
import useMediaQuery from '@mui/material/useMediaQuery'
import makeStyles from '@mui/styles/makeStyles'
import { Link } from 'react-router-dom'

const useStyles = makeStyles(theme => ({
  links: {
    display: 'flex',
    fontSize: '0.75rem',
    paddingBottom: theme.spacing(2),
    paddingLeft: theme.spacing(1),
    paddingTop: theme.spacing(2),
    [theme.breakpoints.down('sm')]: {
      flexDirection: 'column'
    }
  },
  root: {
    backgroundColor: theme.palette.primary.main,
    minHeight: '80px'
  }
}))

const VerticalDivider: React.FunctionComponent = () => {
  return <div style={{ color: '#FFFFFF' }}>|</div>
}

const StyledLink = styled(Link)(({ theme }) => ({
  color: '#FFFFFF',
  paddingLeft: theme.spacing(1),
  paddingRight: theme.spacing(1),
  textDecoration: 'none'
}))

const Footer: React.FunctionComponent = () => {
  const classes = useStyles()
  const theme = useTheme()
  const isLarge = useMediaQuery(theme.breakpoints.up('sm'))

  return (
    <div className={classes.root}>
      <div className={classes.links}>
        <StyledLink to={{ pathname: '/' }}>Home</StyledLink>
        {isLarge && <VerticalDivider />}
        <StyledLink to={{ pathname: '/' }}>Disclaimer</StyledLink>
        {isLarge && <VerticalDivider />}
        <StyledLink to={{ pathname: '/' }}>Privacy</StyledLink>
        {isLarge && <VerticalDivider />}
        <StyledLink to={{ pathname: '/' }}>Accessibility</StyledLink>
        {isLarge && <VerticalDivider />}
        <StyledLink to={{ pathname: '/' }}>Copyright</StyledLink>
        {isLarge && <VerticalDivider />}
        <StyledLink
          to="#"
          onClick={e => {
            window.location.href = 'mailto:BCWS.PredictiveServices@gov.bc.ca'
            e.preventDefault()
          }}
        >
          Contact Us
        </StyledLink>
      </div>
    </div>
  )
}

export default React.memo(Footer)
