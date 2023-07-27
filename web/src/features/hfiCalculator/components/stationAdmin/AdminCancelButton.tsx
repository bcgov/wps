import React from 'react'
import { styled } from '@mui/material/styles'
import { Button } from '@mui/material'
import { theme } from 'app/theme'

const PREFIX = 'AdminCancelButton'

const classes = {
  actionButton: `${PREFIX}-actionButton`
}

const StyledButton = styled(Button)(() => ({
  [`&.${classes.actionButton}`]: {
    minWidth: 100,
    margin: theme.spacing(1),
    float: 'right'
  }
}))

export interface AdminCancelButtonProps {
  testId?: string
  handleCancel: () => void
}

const AdminCancelButton = ({ handleCancel }: AdminCancelButtonProps) => {
  return (
    <StyledButton
      data-testid={'cancel-new-station-button'}
      variant="outlined"
      color="primary"
      className={classes.actionButton}
      onClick={handleCancel}
    >
      Cancel
    </StyledButton>
  )
}

export default React.memo(AdminCancelButton)
