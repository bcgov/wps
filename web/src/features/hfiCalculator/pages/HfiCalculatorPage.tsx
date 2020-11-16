import React from 'react'
import { Container, PageHeader, PageTitle } from 'components'

const HfiCalculatorPage: React.FunctionComponent = () => {
  return (
    <main data-testid="hfi-calculator-page">
      <PageHeader title="Predictive Services Unit" />
      <PageTitle title="HFI Calculator" />
      <Container>Hello World!</Container>
    </main>
  )
}

export default React.memo(HfiCalculatorPage)
