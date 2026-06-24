import { Container as C, type ContainerProps } from '@mui/material'
import type React from 'react'

export const Container: React.FunctionComponent<ContainerProps> = (props: ContainerProps) => {
  return <C maxWidth="md" {...props} />
}

type OptionalContainerProps = ContainerProps & { noContainer?: boolean }
export const OptionalContainer = (props: OptionalContainerProps): JSX.Element => {
  if (props.noContainer) {
    return <div className={props.className}>{props.children}</div>
  }

  return <C maxWidth="md" {...props} />
}
