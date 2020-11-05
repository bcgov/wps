import React from 'react'
import { makeStyles } from '@material-ui/core/styles'

interface Props {
  error: string
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

export const ErrorMessage: React.FunctionComponent<Props> = (props: Props) => {
  const classes = useStyles(props)
  const message = props.context ? `Error occurred (${props.context}).` : 'Error occurred.'

  return (
    <div className={classes.root} data-testid="error-message">
      {message}
    </div>
  )
}
