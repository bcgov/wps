import React from 'react'
import { makeStyles, Theme } from '@material-ui/core/styles'

const useStyles = makeStyles<Theme>(theme => ({
  root: {
    color: theme.palette.error.main,
    marginTop: (props: any) => props.marginTop // eslint-disable-line @typescript-eslint/no-explicit-any
  }
}))

interface Props {
  message: string
  when?: string
  marginTop?: number
}

export const ErrorMessage = (props: Props) => {
  const classes = useStyles(props)

  return (
    <div className={classes.root}>
      {props.message} ({props.when})
    </div>
  )
}
