import { TableCell, Skeleton } from '@mui/material'
import React from 'react'

export interface LoadingIndicatorCellProps {
  loading: boolean
  rowUpdating: boolean
  initialLoad: boolean
  children?: React.ReactNode
}

const LoadingIndicatorCell = (props: LoadingIndicatorCellProps) => {
  const showLoadingIndicator = props.loading && (props.rowUpdating || props.initialLoad)
  return (
    <React.Fragment>
      {showLoadingIndicator ? (
        <TableCell data-testid="loading-indicator-fba">
          <Skeleton />
        </TableCell>
      ) : (
        props.children
      )}
    </React.Fragment>
  )
}

export default React.memo(LoadingIndicatorCell)
