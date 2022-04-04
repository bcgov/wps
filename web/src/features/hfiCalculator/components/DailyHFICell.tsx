import HFICell from 'components/HFICell'
import CalculatedCell from 'features/hfiCalculator/components/CalculatedCell'
import React from 'react'

export interface DailyHFICellProps {
  testid: string | undefined
  value: string | undefined
  error: boolean
  className: string | undefined
}

export const DailyHFICell = (props: DailyHFICellProps) => {
  if (props.error) {
    return <CalculatedCell {...props} />
  }
  return <HFICell testId={props.testid} value={Number(props.value)} />
}
