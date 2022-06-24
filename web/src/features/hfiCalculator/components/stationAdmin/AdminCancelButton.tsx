import React from 'react'
import { Button } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import { theme } from 'app/theme'

export interface AdminCancelButtonProps {
  testId?: string
  handleCancel: () => void
}

const useStyles = makeStyles(() => ({
  actionButton: {
    minWidth: 100,
    margin: theme.spacing(1),
    float: 'right'
  }
}))

const AdminCancelButton = ({ handleCancel }: AdminCancelButtonProps) => {
  const classes = useStyles()

  return (
    <Button
      data-testid={'cancel-new-station-button'}
      variant="outlined"
      color="primary"
      className={classes.actionButton}
      onClick={handleCancel}
    >
      Cancel
    </Button>
  )
}

export default React.memo(AdminCancelButton)
