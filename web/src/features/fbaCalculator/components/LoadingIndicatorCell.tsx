import { TableCell } from '@material-ui/core'
import { Skeleton } from '@material-ui/lab'
import React from 'react'

export interface LoadingIndicatorCellProps {
  loading: boolean
  rowUpdating: boolean
  initialLoad: boolean
  children?: React.ReactNode
}

const LoadingIndicatorCell = (props: LoadingIndicatorCellProps) => {
  const showLoadingIndicator =
    (props.loading && props.rowUpdating) || (props.initialLoad && props.loading)
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
