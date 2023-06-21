import React from 'react'
import { styled } from '@mui/material/styles'
import { isEmpty } from 'lodash'
import { LockOutlined, LockOpenOutlined } from '@mui/icons-material'

const PREFIX = 'LoggedInStatus'

const classes = {
  root: `${PREFIX}-root`
}

const Root = styled('div')(() => ({
  [`&.${classes.root}`]: {
    display: 'flex',
    alignItems: 'center'
  }
}))

export interface LoggedInStatusProps {
  isAuthenticated: boolean
  roles: string[]
  idir: string | undefined
}

const LoggedInStatus = ({ isAuthenticated, roles, idir }: LoggedInStatusProps) => {
  if (!isAuthenticated) {
    return <React.Fragment></React.Fragment>
  }

  if (isAuthenticated && isEmpty(roles)) {
    return (
      <Root data-testid="logged-in-status" className={classes.root}>
        <LockOutlined />
        Read only: {idir}
      </Root>
    )
  }

  return (
    <div data-testid="logged-in-status" className={classes.root}>
      <LockOpenOutlined />
      Editing: {idir}
    </div>
  )
}

export default React.memo(LoggedInStatus)
