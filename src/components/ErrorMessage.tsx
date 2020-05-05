import React from 'react'
import { makeStyles } from '@material-ui/core/styles'

const useStyles = makeStyles(theme => ({
  root: {
    color: theme.palette.error.main,
    marginTop: (props: any) => props.marginTop // eslint-disable-line @typescript-eslint/no-explicit-any
  }
}))

interface Props {
  error: string
  context?: string
  marginTop?: number
}

export const ErrorMessage = (props: Props) => {
  const classes = useStyles(props)
  const message = props.context ? `Error occurred (${props.context}).` : 'Error occurred.'

  return <div className={classes.root}>{message}</div>
}
