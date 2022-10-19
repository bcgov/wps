import React from 'react'
import makeStyles from '@mui/styles/makeStyles'

import HeaderImage from './HeaderImage'
import Contact from './Contact'
import { theme } from 'app/theme'

import { OptionalContainer } from 'components/Container'

const useStyles = makeStyles(() => ({
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
  padding?: number
}

export const PercentileHeader: React.FunctionComponent<Props> = (props: Props) => {
  const { title, productName } = props
  const classes = useStyles(props)

  return (
    <nav className={classes.root}>
      <OptionalContainer className={classes.container}>
        <div className={classes.titleWrapper}>
          <HeaderImage />
          <div className={classes.title}>{title}</div>
        </div>
        <Contact productName={productName}></Contact>
      </OptionalContainer>
    </nav>
  )
}
