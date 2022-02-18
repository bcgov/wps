import { TableCell } from '@material-ui/core'
import ErrorIconWithTooltip from 'features/hfiCalculator/components/ErrorIconWithTooltip'
import { DECIMAL_PLACES } from 'features/hfiCalculator/constants'
import { ValidatedStationDaily } from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import { isNull, isUndefined } from 'lodash'
import React, { ReactElement } from 'react'

export interface RequiredDataCellProps {
  testId?: string
  classNameForRow?: string
  daily: ValidatedStationDaily | undefined
  dailyKey: keyof ValidatedStationDaily
  errorToolTipText: string
}

export const RequiredDataCell = ({
  testId,
  classNameForRow,
  daily,
  dailyKey,
  errorToolTipText
}: RequiredDataCellProps): ReactElement => {
  const dataValue = daily ? Number(daily[dailyKey])?.toFixed(DECIMAL_PLACES) : ''

  return (
    <React.Fragment>
      {(daily && isUndefined(daily[dailyKey])) || (daily && isNull(daily[dailyKey])) ? (
        <TableCell data-testid={testId}>
          <ErrorIconWithTooltip
            isDataCell={true}
            tooltipElement={<div>{errorToolTipText}</div>}
            tooltipAriaText={[errorToolTipText]}
          />
        </TableCell>
      ) : (
        <TableCell className={classNameForRow}>{dataValue}</TableCell>
      )}
    </React.Fragment>
  )
}

export default React.memo(RequiredDataCell)
