import React from 'react'
import clsx from 'clsx'
import { Button as B, ButtonProps, CircularProgress } from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'

interface CustomProps {
  loading?: boolean
}

type Props = CustomProps & ButtonProps

const useStyles = makeStyles(theme => ({
  root: {
    position: 'relative'
  },
  spinner: {
    color: theme.palette.primary.light,
    position: 'absolute'
  }
}))

export const Button = ({ loading, ...buttonProps }: Props) => {
  const classes = useStyles()
  const buttonClassName = clsx(classes.root, buttonProps.className)

  return (
    <B className={buttonClassName} {...buttonProps}>
      {buttonProps.children}
      {loading && <CircularProgress size={24} className={classes.spinner} />}
    </B>
  )
}
