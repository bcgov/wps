import { TableCell } from '@mui/material'
import { styled } from '@mui/material/styles'
import { theme } from 'app/theme'
import React from 'react'

const PREFIX = 'StickyCell'

const classes = {
  sticky: `${PREFIX}-sticky`
}

const StyledTableCell = styled(TableCell, {
  shouldForwardProp: prop => prop !== 'zIndexOffset'
})((props: Pick<StickyCellProps, 'left' | 'zIndexOffset' | 'backgroundColor'>) => ({
  [`& .${classes.sticky}`]: {
    left: props.left,
    position: 'sticky',
    zIndex: theme.zIndex.appBar + props.zIndexOffset,
    backgroundColor: props.backgroundColor ? props.backgroundColor : undefined
  }
}))

interface StickyCellProps {
  left: number
  zIndexOffset: number
  children?: React.ReactNode
  backgroundColor?: string
  testId?: string
  colSpan?: number
  className?: string
}

const StickyCell = (props: StickyCellProps) => {
  return (
    <StyledTableCell
      data-testid={`stickyCell-fba`}
      className={`${classes.sticky} ${props.className}`}
      colSpan={props.colSpan}
      left={0}
      zIndexOffset={0}
    >
      {props.children}
    </StyledTableCell>
  )
}

export default React.memo(StickyCell)
