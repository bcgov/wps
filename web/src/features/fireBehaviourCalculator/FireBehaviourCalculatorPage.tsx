import { Container, PageHeader } from 'components'
import React from 'react'
import FBCFormControl from './components/FBCFormControl'

export const FireBehaviourCalculator: React.FunctionComponent = () => {
  return (
    <main>
      <PageHeader
        title="Predictive Services Unit"
        productName="Predictive Services Unit"
      />
      <Container>
        <h1>Fire Behavior Calculator WIP</h1>
        <FBCFormControl />
      </Container>
    </main>
  )
}
