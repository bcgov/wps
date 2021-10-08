import { Icon, TableCell, Tooltip } from '@material-ui/core'
import InfoOutlinedIcon from '@material-ui/icons/InfoOutlined'
import React from 'react'
export interface FireTypeCellProps {
  fireType: string | undefined
}

const toolTipFirstLine = 'SUR = Surface Type'
const toolTipSecondLine = 'IC = Intermittent Crown Type'
const toolTipThirdLine = 'CC = Continuous Crown Type'
const toolTipElement = (
  <div>
    {toolTipFirstLine} <br />
    {toolTipSecondLine} <br />
    {toolTipThirdLine}
  </div>
)

const FireTypeCell = (props: FireTypeCellProps) => {
  return <TableCell>{props?.fireType}</TableCell>
}

export default React.memo(FireTypeCell)
