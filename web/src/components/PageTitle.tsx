import React from 'react'
import { makeStyles } from '@material-ui/core/styles'

import { Container } from 'components/Container'

const useStyles = makeStyles(theme => ({
  root: {
    maxHeight: 60,
    marginBottom: '1rem',
    paddingBottom: '1rem',
    paddingTop: '1rem',
    fontSize: '1.3rem',
    background: theme.palette.primary.light,
    color: theme.palette.primary.contrastText
  }
}))

interface Props {
  title: string
}

export const PageTitle: React.FunctionComponent<Props> = ({ title }: Props) => {
  const classes = useStyles()

  return (
    <div className={classes.root}>
      <Container>{title}</Container>
    </div>
  )
}
