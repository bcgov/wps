import { TableCell, TableRow } from '@material-ui/core'
import React from 'react'

export interface YesterdayActualIndices {
  ffmc?: number
  dmc?: number
  dc?: number
}

export interface YesterdayIndicesProps {
  isLoading: boolean
  yesterdayActuals?: YesterdayActualIndices
}

const YesterdayIndices = ({ yesterdayActuals }: YesterdayIndicesProps) => {
  return (
    <React.Fragment>
      <TableRow>
        <TableCell>Yesterday&apos;s FFMC</TableCell>
        <TableCell>{yesterdayActuals?.ffmc}</TableCell>
      </TableRow>
      <TableRow>
        <TableCell>Yesterday&apos;s DMC</TableCell>
        <TableCell>{yesterdayActuals?.dmc}</TableCell>
      </TableRow>
      <TableRow>
        <TableCell>Yesterday&apos;s DC</TableCell>
        <TableCell>{yesterdayActuals?.dc}</TableCell>
      </TableRow>
    </React.Fragment>
  )
}
export default React.memo(YesterdayIndices)
