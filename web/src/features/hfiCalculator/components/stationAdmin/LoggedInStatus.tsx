import React from 'react'
import { styled } from '@mui/material/styles'
import { isEmpty } from 'lodash'
import { LockOutlined, LockOpenOutlined } from '@mui/icons-material'

const PREFIX = 'LoggedInStatus'

const Root = styled('div', {
  name: `${PREFIX}-root`
})({
  display: 'flex',
  alignItems: 'center'
})

export interface LoggedInStatusProps {
  isAuthenticated: boolean
  roles: string[]
  idir: string | undefined
}

const LoggedInStatus = ({ isAuthenticated, roles, idir }: LoggedInStatusProps) => {
  if (!isAuthenticated) {
    return <></>
  }

  if (isAuthenticated && isEmpty(roles)) {
    return (
      <Root data-testid="logged-in-status">
        <LockOutlined />
        Read only: {idir}
      </Root>
    )
  }

  return (
    <Root data-testid="logged-in-status">
      <LockOpenOutlined />
      Editing: {idir}
    </Root>
  )
}

export default React.memo(LoggedInStatus)
