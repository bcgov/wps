import { selectFireBehaviourCalcResult } from 'app/rootReducer'
import { Container, PageHeader } from 'components'
import { DateTime } from 'luxon'
import React, { useState } from 'react'
import { useSelector } from 'react-redux'
import FBCInputForm from './components/FBCInputForm'
import FBCResultTable from './components/FBCResultTable'

export const FireBehaviourCalculator: React.FunctionComponent = () => {
  const [dateOfInterest, setDateOfInterest] = useState(DateTime.now().toISODate())
  const [stationsOfInterest, setStationsOfInterest] = useState(322)
  const [fuelType, setFuelType] = useState('')
  const [grassCurePercentage, setGrassCurePercentage] = useState<number | null>(null)

  const { fireBehaviourResultStations } = useSelector(selectFireBehaviourCalcResult)

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

        {fireBehaviourResultStations.length > 0 && (
          <FBCResultTable
            testId="fb-calc-result-table"
            fireBehaviourResultStations={fireBehaviourResultStations}
          />
        )}
      </Container>
    </main>
  )
}
