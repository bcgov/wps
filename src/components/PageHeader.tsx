import React from 'react'
import { Container } from 'components/Container'
import { makeStyles } from '@material-ui/core/styles'

const useStyles = makeStyles({
  root: {
    maxHeight: 60
  },
  logo: {
    width: 180,
    height: 45
  }
})

export const PageHeader = () => {
  const classes = useStyles()

  return (
    <nav className={classes.root}>
      <Container>
        <a href="https://www2.gov.bc.ca">
          <img
            className={classes.logo}
            src={process.env.PUBLIC_URL + '/images/bcid-logo-rev-en.svg'}
            alt="B.C. Government logo"
          />
        </a>
      </Container>
    </nav>
  )
}
