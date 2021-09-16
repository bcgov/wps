import React from 'react'
import { makeStyles } from '@material-ui/core/styles'

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
  container: () => ({
    display: 'flex',
    alignItems: 'center',
    maxWidth: '100%'
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
  const { title, productName, spacing, padding } = props
  const classes = useStyles(props)

  return (
    <nav className={classes.root}>
      <OptionalContainer style={{ paddingLeft: padding }} className={classes.container}>
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
