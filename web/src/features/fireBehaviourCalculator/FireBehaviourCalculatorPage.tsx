import { Container, PageHeader } from 'components'
import { DateTime } from 'luxon'
import React, { useState } from 'react'
import FBCInputForm from './components/FBCFormControl'
import FBCResultTable from './components/FBCResultTable'

export const FireBehaviourCalculator: React.FunctionComponent = () => {
  const [dateOfInterest, setDateOfInterest] = useState(DateTime.now().toISODate())
  const [stationsOfInterest, setStationsOfInterest] = useState([] as number[])
  const [fuelType, setFuelType] = useState('')
  const [grassCurePercentage, setGrassCurePercentage] = useState(0)

  return (
    <main>
      <PageHeader
        title="Predictive Services Unit"
        productName="Predictive Services Unit"
      />
      <Container maxWidth={'xl'}>
        <h1>Fire Behavior Calculator Prototype</h1>
        <FBCInputForm
          dateOfInterest={dateOfInterest}
          setDateOfInterest={setDateOfInterest}
          stationsOfInterest={stationsOfInterest}
          setStationsOfInterest={setStationsOfInterest}
          fuelType={fuelType}
          setFuelType={setFuelType}
          grassCurePercentage={grassCurePercentage}
          setGrassCurePercentage={setGrassCurePercentage}
        />
        <FBCResultTable testId="hfi-calc-daily-table" />
      </Container>
    </main>
  )
}
