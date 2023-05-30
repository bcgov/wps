import React from 'react'
import makeStyles from '@mui/styles/makeStyles'

import HeaderImage from './HeaderImage'
import Contact from './Contact'

import { OptionalContainer } from 'components/Container'

const useStyles = makeStyles(theme => ({
  beta: {
    alignSelf: 'flex-start',
    color: theme.palette.secondary.main,
    fontSize: '1.25em',
    fontWeight: 'bold',
    paddingLeft: theme.spacing(1),
    paddingTop: theme.spacing(2)
  },
  root: {
    background: theme.palette.primary.main,
    borderBottomWidth: 2,
    borderBottomStyle: 'solid',
    borderBottomColor: theme.palette.secondary.main,
    marginBottom: theme.spacing(1)
  },
  container: (props: Props) => ({
    display: 'flex',
    alignItems: 'center',
    maxWidth: '100%',
    paddingLeft: props.padding
  }),
  title: {
    color: theme.palette.primary.contrastText,
    fontSize: '1.7rem'
  },
  titleWrapper: {
    display: 'flex',
    alignItems: 'center'
  }
}))

interface Props {
  isBeta: boolean
  padding?: string
  productName: string
  spacing: number
  title: string
}

export const GeneralHeader: React.FunctionComponent<Props> = (props: Props) => {
  const { title, productName, spacing } = props
  const classes = useStyles(props)

  return (
    <nav className={classes.root}>
      <OptionalContainer className={classes.container}>
        <div className={classes.titleWrapper}>
          <HeaderImage />
          <div className={classes.title}>{title}</div>
          {props.isBeta && <div className={classes.beta}>BETA</div>}
        </div>
        <div style={{ flexGrow: spacing }}></div>
        <Contact productName={productName}></Contact>
      </OptionalContainer>
    </nav>
  )
}
