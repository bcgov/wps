import React from 'react'

import { Button } from '@mui/material'
import { theme } from 'app/theme'
import styled from '@emotion/styled'

const StyledButton = styled(Button)(({ selected }: { selected: boolean }) => ({
  marginLeft: theme.spacing(1),
  border: `solid ${selected ? '2px' : '1px'}`,
  borderColor: 'black',
  color: 'black',
  '&:hover': {
    color: 'black',
    backgroundColor: 'white'
  }
}))

interface SelectableButtonProps {
  children?: React.ReactNode
  dataTestId?: string
  onClick: () => void
  selected: boolean
  className?: string
}

const SelectableButton = ({ children, dataTestId, onClick, selected, className }: SelectableButtonProps) => {
  return (
    <StyledButton
      data-testid={dataTestId}
      onClick={onClick}
      variant={selected ? 'contained' : 'outlined'}
      selected={selected}
      className={className}
    >
      {children}
    </StyledButton>
  )
}

export default React.memo(SelectableButton)
