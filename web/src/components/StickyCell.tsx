import { TableCell } from '@mui/material'
import { styled } from '@mui/material/styles'
import { theme } from 'app/theme'
import React from 'react'

const StyledTableCell = styled(TableCell, {
  shouldForwardProp: prop => prop !== 'zIndexOffset' && prop !== 'backgroundColor'
})((props: Pick<StickyCellProps, 'left' | 'zIndexOffset' | 'backgroundColor'>) => ({
  left: props.left,
  position: 'sticky',
  zIndex: theme.zIndex.appBar + props.zIndexOffset,
  backgroundColor: props.backgroundColor ? props.backgroundColor : undefined
}))

interface StickyCellProps {
  left: number
  zIndexOffset: number
  children?: React.ReactNode
  backgroundColor?: string
  colSpan?: number
  className?: string
}

const StickyCell = (props: StickyCellProps) => {
  return (
    <StyledTableCell
      data-testid={`stickyCell-fba`}
      className={props.className}
      colSpan={props.colSpan}
      left={props.left}
      zIndexOffset={props.zIndexOffset}
      backgroundColor={props.backgroundColor}
    >
      {props.children}
    </StyledTableCell>
  )
}

export default React.memo(StickyCell)
