import React from 'react'

import { Container, PageHeader, PageTitle } from 'components'
import DailyViewTable from '../components/DailyViewTable'

const HfiCalculatorPage: React.FunctionComponent = () => {
  return (
    <main data-testid="hfi-calculator-page">
      <PageHeader title="Predictive Services Unit" productName="HFI Calculator" />
      <PageTitle title="HFI Calculator" />
      <Container maxWidth={'xl'}>
        <DailyViewTable title={'Daily View Table'} stationData={[]}></DailyViewTable>
      </Container>
    </main>
  )
}

export default React.memo(HfiCalculatorPage)
