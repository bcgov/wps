import React from 'react'

import { Button } from '@mui/material'
import { theme } from 'app/theme'

interface SelectableButtonProps {
  children?: React.ReactNode
  onClick: () => void
  selected: boolean
}

const SelectableButton = ({ children, onClick, selected }: SelectableButtonProps) => {
  return (
    <Button sx={{ marginLeft: theme.spacing(1) }} onClick={onClick} variant={selected ? 'contained' : 'outlined'}>
      {children}
    </Button>
  )
}

export default React.memo(SelectableButton)
