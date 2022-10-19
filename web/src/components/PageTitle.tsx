import React from 'react'
import { makeStyles } from '@mui/styles'
import { theme } from 'app/theme'
import { Container } from 'components/Container'

const useStyles = makeStyles(() => ({
  root: (props: Props) => ({
    maxHeight: 60,
    marginBottom: '1rem',
    paddingBottom: '1rem',
    paddingTop: '1rem',
    paddingLeft: props.padding,
    fontSize: '1.3rem',
    background: theme.palette.primary.light,
    color: theme.palette.primary.contrastText
  })
}))

interface Props {
  title: string
  padding?: string
  maxWidth?: false | 'xs' | 'sm' | 'md' | 'lg' | 'xl' | undefined
}

export const PageTitle: React.FunctionComponent<Props> = (props: Props) => {
  const classes = useStyles(props)
  const { title, maxWidth } = props

  return (
    <div className={classes.root}>
      {maxWidth !== undefined ? <Container maxWidth={maxWidth}>{title}</Container> : <Container>{title}</Container>}
    </div>
  )
}
