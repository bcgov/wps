import { TableCell } from '@material-ui/core'
import { Skeleton } from '@material-ui/lab'
import React from 'react'

interface LoadingIndicatorCellProps {
  loading: boolean
  children?: React.ReactNode
}

const LoadingIndicatorCell = (props: LoadingIndicatorCellProps) => (
  <React.Fragment>
    {props.loading ? (
      <TableCell>
        <Skeleton />
      </TableCell>
    ) : (
      props.children
    )}
  </React.Fragment>
)

export default React.memo(LoadingIndicatorCell)
