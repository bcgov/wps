import React from 'react'

import { Button } from '@mui/material'

interface SelectableButtonProps {
  children?: React.ReactNode
  className: string
  onClick: () => void
  selected: boolean
}

const SelectableButton = ({ children, className, onClick, selected }: SelectableButtonProps) => {
  return (
    <Button className={className} onClick={onClick} variant={selected ? 'contained' : 'outlined'}>
      {children}
    </Button>
  )
}

export default React.memo(SelectableButton)
