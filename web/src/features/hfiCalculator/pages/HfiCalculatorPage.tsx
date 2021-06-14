import React, { useEffect } from 'react'

import { Container, PageHeader, PageTitle } from 'components'
import DailyViewTable from '../components/DailyViewTable'
import { fetchHFIDailies } from '../slices/hfiCalculatorSlice'
import { useDispatch, useSelector } from 'react-redux'
import { DateTime } from 'luxon'
import { selectHFIDailies } from 'app/rootReducer'
import { makeStyles, CircularProgress } from '@material-ui/core'

const HfiCalculatorPage: React.FunctionComponent = () => {
  const useStyles = makeStyles({
    container: {
      display: 'flex',
      justifyContent: 'center'
    }
  })
  const classes = useStyles()

  const dispatch = useDispatch()
  const { dailies, loading } = useSelector(selectHFIDailies)
  useEffect(() => {
    // For now just give dailies for today
    const startTime = DateTime.now()
      .startOf('day')
      .toUTC()
      .valueOf()
    const endTime = DateTime.now()
      .endOf('day')
      .toUTC()
      .valueOf()
    dispatch(fetchHFIDailies(startTime, endTime))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])
  return (
    <main data-testid="hfi-calculator-page">
      <PageHeader title="Predictive Services Unit" productName="HFI Calculator" />
      <PageTitle title="HFI Calculator" />
      <Container className={classes.container} maxWidth={'xl'}>
        {loading ? (
          <CircularProgress />
        ) : (
          <DailyViewTable
            title={'Daily View Table'}
            stationData={dailies}
          ></DailyViewTable>
        )}
      </Container>
    </main>
  )
}

export default React.memo(HfiCalculatorPage)
