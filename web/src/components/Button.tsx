import React, { forwardRef } from 'react'
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
    position: 'absolute',
    left: '50%',
    marginLeft: -10,
    top: '50%',
    marginTop: -10
  }
}))

/* eslint-disable react/prop-types, react/display-name */
// Use forwardRef to obtain the ref passed to it, and then forward it to the DOM button that it renders.
// https://medium.com/@martin_hotell/react-refs-with-typescript-a32d56c4d315
export const Button = forwardRef<HTMLButtonElement, Props>((props, ref) => {
  const { loading, className, disabled, ...buttonProps } = props
  const classes = useStyles()
  const buttonClassName = clsx(classes.root, className)

  return (
    <B
      {...buttonProps}
      className={buttonClassName}
      disabled={disabled || loading}
      ref={ref}
    >
      {buttonProps.children}
      {loading && <CircularProgress size={20} className={classes.spinner} />}
    </B>
  )
})
