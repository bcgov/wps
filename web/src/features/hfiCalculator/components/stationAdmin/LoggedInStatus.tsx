import React from 'react'
import LockIcon from '@mui/icons-material/Lock'
import LockOpenIcon from '@mui/icons-material/LockOpen'
import makeStyles from '@mui/styles/makeStyles'
import { isEmpty } from 'lodash'

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
        <LockIcon></LockIcon>
        {idir}
      </div>
    )
  }

  return (
    <div data-testid="logged-in-status" className={classes.root}>
      <LockOpenIcon></LockOpenIcon>
      {idir}
    </div>
  )
}

export default React.memo(LoggedInStatus)
