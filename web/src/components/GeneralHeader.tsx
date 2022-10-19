import React from 'react'
import makeStyles from '@mui/styles/makeStyles'

import HeaderImage from './HeaderImage'
import Contact from './Contact'

import { OptionalContainer } from 'components/Container'

const useStyles = makeStyles(theme => ({
  root: {
    background: theme.palette.primary.main,
    borderBottomWidth: 2,
    borderBottomStyle: 'solid',
    borderBottomColor: theme.palette.secondary.main
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
  title: string
  productName: string
  padding?: string
  spacing: number
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
        </div>
        <div style={{ flexGrow: spacing }}></div>
        <Contact productName={productName}></Contact>
      </OptionalContainer>
    </nav>
  )
}
