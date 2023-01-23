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

const StyledA = styled('a')(({ theme }) => ({
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
        <StyledA href="https://www2.gov.bc.ca/gov/content/home/disclaimer" rel="noreferrer" target="_blank">
          Disclaimer
        </StyledA>
        {isLarge && <VerticalDivider />}
        <StyledA href="https://www2.gov.bc.ca/gov/content/home/privacy" rel="noreferrer" target="_blank">
          Privacy
        </StyledA>
        {isLarge && <VerticalDivider />}
        <StyledA href="https://www2.gov.bc.ca/gov/content/home/accessible-government" rel="noreferrer" target="_blank">
          Accessibility
        </StyledA>
        {isLarge && <VerticalDivider />}
        <StyledA href="https://www2.gov.bc.ca/gov/content/home/copyright" rel="noreferrer" target="_blank">
          Copyright
        </StyledA>
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
