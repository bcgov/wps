import { Container, PageHeader } from 'components'
import React from 'react'
import FBCInputForm from './components/FBCFormControl'
import FBCResultTable from './components/FBCResultTable'

export const FireBehaviourCalculator: React.FunctionComponent = () => {
  return (
    <main>
      <PageHeader
        title="Predictive Services Unit"
        productName="Predictive Services Unit"
      />
      <Container maxWidth={'xl'}>
        <h1>Fire Behavior Calculator Prototype</h1>
        <FBCInputForm />
        <FBCResultTable testId="hfi-calc-daily-table" />
      </Container>
    </main>
  )
}
