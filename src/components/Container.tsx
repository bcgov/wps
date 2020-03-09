import React from 'react'
import { Container as C, ContainerProps } from '@material-ui/core'

export const Container = (props: ContainerProps) => {
  return <C maxWidth="md" {...props} />
}
