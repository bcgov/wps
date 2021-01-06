import React from 'react'
import { Container } from 'components/Container'
import { makeStyles } from '@material-ui/core/styles'

const useStyles = makeStyles(theme => ({
  root: {
    background: theme.palette.primary.main,
    borderBottomWidth: 2,
    borderBottomStyle: 'solid',
    borderBottomColor: theme.palette.secondary.main
  },
  container: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between'
  },
  logo: {
    width: 175,
    marginTop: '10px',
    marginBottom: '10px'
  },
  title: {
    color: theme.palette.primary.contrastText,
    fontSize: '1.7rem'
  },
  titleWrapper: {
    display: 'flex',
    alignItems: 'center'
  },
  contact: {
    color: 'white',
    fontStyle: 'bold',
    fontSize: '1.1em',
    textDecoration: 'none',
    '&:hover': {
      textDecoration: 'underline'
    }
  }
}))

interface Props {
  title: string
}

export const PageHeader: React.FunctionComponent<Props> = ({ title }: Props) => {
  const classes = useStyles()

  return (
    <nav className={classes.root}>
      <Container className={classes.container}>
        <div className={classes.titleWrapper}>
          <a href="https://gov.bc.ca">
            <img
              className={classes.logo}
              src={'/images/BCID_H_rgb_rev.svg'}
              alt="B.C. Government logo"
            />
          </a>
          <div className={classes.title}>{title}</div>
        </div>
        <div
          className={classes.contact}
          onClick={() => window.open('mailto:bcws.predictiveservice@gov.bc.ca')}
        >
          Contact
        </div>
      </Container>
    </nav>
  )
}
