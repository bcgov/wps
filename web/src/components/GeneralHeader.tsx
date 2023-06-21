import React from 'react'
import { styled } from '@mui/material/styles'

import HeaderImage from './HeaderImage'
import Contact from './Contact'

import { OptionalContainer } from 'components/Container'

const PREFIX = 'GeneralHeader'

const classes = {
  beta: `${PREFIX}-beta`,
  root: `${PREFIX}-root`,
  container: `${PREFIX}-container`,
  title: `${PREFIX}-title`,
  titleWrapper: `${PREFIX}-titleWrapper`
}

const Root = styled('nav')(({ theme }) => ({
  [`& .${classes.beta}`]: {
    alignSelf: 'flex-start',
    color: theme.palette.secondary.main,
    fontSize: '1.25em',
    fontWeight: 'bold',
    paddingLeft: theme.spacing(1),
    paddingTop: theme.spacing(2)
  },

  [`&.${classes.root}`]: {
    background: theme.palette.primary.main,
    borderBottomWidth: 2,
    borderBottomStyle: 'solid',
    borderBottomColor: theme.palette.secondary.main
  },

  [`& .${classes.container}`]: (props: Props) => ({
    display: 'flex',
    alignItems: 'center',
    maxWidth: '100%',
    paddingLeft: props.padding
  }),

  [`& .${classes.title}`]: {
    color: theme.palette.primary.contrastText,
    fontSize: '1.7rem'
  },

  [`& .${classes.titleWrapper}`]: {
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

  return (
    <Root className={classes.root}>
      <OptionalContainer className={classes.container}>
        <div className={classes.titleWrapper}>
          <HeaderImage />
          <div className={classes.title}>{title}</div>
          {props.isBeta && <div className={classes.beta}>BETA</div>}
        </div>
        <div style={{ flexGrow: spacing }}></div>
        <Contact productName={productName}></Contact>
      </OptionalContainer>
    </Root>
  )
}
