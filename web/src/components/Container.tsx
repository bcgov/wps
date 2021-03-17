import React from 'react'
import { Container as C, ContainerProps } from '@material-ui/core'

export const Container: React.FunctionComponent<ContainerProps> = (
  props: ContainerProps
) => {
  return <C maxWidth="md" {...props} />
}
