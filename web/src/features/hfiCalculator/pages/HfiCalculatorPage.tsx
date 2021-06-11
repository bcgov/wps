import React, { useEffect } from 'react'

import { Container, PageHeader, PageTitle } from 'components'
import DailyViewTable from 'features/hfiCalculator/components/DailyViewTable'
import { useDispatch } from 'react-redux'
import { fetchHFIStations } from '../slices/stationsSlice'

const HfiCalculatorPage: React.FunctionComponent = () => {
  const dispatch = useDispatch()
  useEffect(() => {
    dispatch(fetchHFIStations())
  })


  return (
    <main data-testid="hfi-calculator-page">
      <PageHeader title="Predictive Services Unit" productName="HFI Calculator" />
      <PageTitle title="HFI Calculator" />
      <Container>
        <DailyViewTable title="HFI Calculator Daily View" testId="hfi-calc-daily-table" />
      </Container>
    </main>
  )
}

export default React.memo(HfiCalculatorPage)
