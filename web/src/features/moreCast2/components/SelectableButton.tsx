import React from 'react'

import { Button } from '@mui/material'
import { theme, MORECAST_COLORS } from 'app/theme'
import styled from '@emotion/styled'

const StyledButton = styled(Button)(({ selected }: { selected: boolean }) => ({
  marginLeft: theme.spacing(1),
  border: `solid ${selected ? '2px' : '1px'}`,
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
  colorClass: keyof typeof MORECAST_COLORS
}

const SelectableButton = ({ children, dataTestId, onClick, selected, colorClass }: SelectableButtonProps) => {
  const { color, fontColor } = MORECAST_COLORS[colorClass] || theme.palette.primary

  return (
    <StyledButton
      data-testid={dataTestId}
      sx={{ backgroundColor: color, color: fontColor }}
      onClick={onClick}
      variant={selected ? 'contained' : 'outlined'}
      selected={selected}
    >
      {children}
    </StyledButton>
  )
}

export default React.memo(SelectableButton)
