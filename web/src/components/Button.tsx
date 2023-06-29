import React, { forwardRef } from 'react'
import { styled } from '@mui/material/styles'
import clsx from 'clsx'
import { Button as B, ButtonProps, CircularProgress } from '@mui/material'
import { theme } from 'app/theme'

const PREFIX = 'Button'

const classes = {
  root: `${PREFIX}-root`,
  spinner: `${PREFIX}-spinner`
}

interface CustomProps {
  loading?: boolean
  hasSpinner?: boolean
  spinnercolor?: string
}

type Props = CustomProps & ButtonProps

/* eslint-disable react/prop-types, react/display-name */
// Use forwardRef to obtain the ref passed to it, and then forward it to the DOM button that it renders.
// https://medium.com/@martin_hotell/react-refs-with-typescript-a32d56c4d315
export const Button = forwardRef<HTMLButtonElement, Props>((props, ref) => {
  const { loading, className, disabled, hasSpinner = true, ...buttonProps } = props

  const StyledB = styled(B)(() => ({
    [`& .${classes.root}`]: {
      position: 'relative'
    },

    [`& .${classes.spinner}`]: {
      color: props.spinnercolor || theme.palette.primary.light,
      position: 'absolute',
      left: '50%',
      marginLeft: -10,
      top: '50%',
      marginTop: -10
    }
  }))

  const buttonClassName = clsx(classes.root, className)

  return (
    <StyledB {...buttonProps} className={buttonClassName} disabled={disabled || loading} ref={ref}>
      {buttonProps.children}
      {loading && hasSpinner && <CircularProgress size={20} className={classes.spinner} />}
    </StyledB>
  )
})
