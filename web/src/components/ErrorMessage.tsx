import React from 'react'
import { makeStyles } from '@material-ui/core/styles'

interface Props {
  error: string
  message?: string
  context?: string
  marginTop?: number
  marginBottom?: number
}

const useStyles = makeStyles(theme => ({
  root: {
    color: theme.palette.error.main,
    marginTop: (props: Props) => props.marginTop,
    marginBottom: (props: Props) => props.marginBottom
  }
}))

const getMessage = ({ message, context }: Props) => {
  if (message) {
    return message
  }

  if (context) {
    return `Error occurred (${context}).`
  }

  return 'Error occurred.'
}

export const ErrorMessage: React.FunctionComponent<Props> = (props: Props) => {
  const classes = useStyles(props)
  const message = getMessage(props)

  return (
    <div className={classes.root} data-testid="error-message">
      {message}
    </div>
  )
}
