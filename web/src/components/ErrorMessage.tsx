import React from 'react'
import { styled } from '@mui/material/styles'
import { theme } from 'app/theme'

const PREFIX = 'ErrorMessage'

const classes = {
  root: `${PREFIX}-root`
}

const Root = styled('div')(() => ({
  [`&.${classes.root}`]: {
    color: theme.palette.error.main,
    marginTop: (props: Props) => props.marginTop,
    marginBottom: (props: Props) => props.marginBottom
  }
}))

interface Props {
  error: string
  message?: string
  context?: string
  marginTop?: number
  marginBottom?: number
}

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
  const message = getMessage(props)

  return (
    <Root className={classes.root} data-testid="error-message">
      {message}
    </Root>
  )
}
