import React from 'react'
import makeStyles from '@mui/styles/makeStyles'
import { isEmpty } from 'lodash'
import { LockOutlined, LockOpenOutlined } from '@mui/icons-material'

export interface LoggedInStatusProps {
  isAuthenticated: boolean
  roles: string[]
  idir: string | undefined
}

const useStyles = makeStyles(() => ({
  root: {
    display: 'flex',
    alignItems: 'center'
  }
}))

const LoggedInStatus = ({ isAuthenticated, roles, idir }: LoggedInStatusProps) => {
  const classes = useStyles()
  if (!isAuthenticated) {
    return <React.Fragment></React.Fragment>
  }

  if (isAuthenticated && isEmpty(roles)) {
    return (
      <div data-testid="logged-in-status" className={classes.root}>
        <LockOutlined />
        Read only: {idir}
      </div>
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
