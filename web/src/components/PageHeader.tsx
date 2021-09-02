import React from 'react'
import { makeStyles } from '@material-ui/core/styles'

import { OptionalContainer } from 'components/Container'

const useStyles = makeStyles(theme => ({
  root: {
    background: theme.palette.primary.main,
    borderBottomWidth: 2,
    borderBottomStyle: 'solid',
    borderBottomColor: theme.palette.secondary.main
  },
  container: () => ({
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingLeft: 'auto',
    paddingRight: 'auto'
  }),
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
    fontSize: '1.2em',
    textDecoration: 'none',
    cursor: 'pointer',

    '&:hover': {
      textDecoration: 'underline'
    }
  }
}))

interface Props {
  title: string
  productName: string
  padding?: number
}

export const PageHeader: React.FunctionComponent<Props> = (props: Props) => {
  const { title, productName } = props
  const classes = useStyles(props)

  return (
    <nav className={classes.root}>
      <OptionalContainer className={classes.container}>
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
        <a
          id="contact-link"
          className={classes.contact}
          href={`mailto:bcws.predictiveservices@gov.bc.ca?subject=Predictive Services Unit - ${productName}`}
        >
          Contact
        </a>
      </OptionalContainer>
    </nav>
  )
}
