import React, { useEffect } from 'react'
import { Container, GeneralHeader } from 'components'
import FBATable from 'features/fbaCalculator/components/FBATable'
import { FIRECALC_DOC_TITLE } from 'utils/constants'
import Footer from '@/features/landingPage/components/Footer'
import { Box } from '@mui/material'

const FireBehaviourCalculator: React.FunctionComponent = () => {
  useEffect(() => {
    document.title = FIRECALC_DOC_TITLE
  }, [])

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <GeneralHeader isBeta={false} spacing={1} title="Fire Behaviour Calculator" />
      <Container sx={{ flexDirection: 'column', flexGrow: 1, paddingTop: '0.5em' }} maxWidth={'xl'}>
        <FBATable />
      </Container>
      <Footer />
    </Box>
  )
}
export default FireBehaviourCalculator
