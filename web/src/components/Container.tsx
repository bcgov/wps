import React from 'react'
import { Container as C, ContainerProps } from '@material-ui/core'

export const Container: React.FunctionComponent<ContainerProps> = (
  props: ContainerProps
) => {
  return <C maxWidth="md" {...props} />
}

type OptionalContainerProps = ContainerProps & { noContainer?: boolean }
export const OptionalContainer = (props: OptionalContainerProps) => {
  if (props.noContainer) {
    return <div className={props.className}>{props.children}</div>
  }

  return <C maxWidth="md" {...props} />
}
