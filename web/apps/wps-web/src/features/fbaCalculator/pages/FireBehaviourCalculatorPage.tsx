import { Box } from '@mui/material'
import { Container } from '@wps/ui/Container'
import { GeneralHeader } from '@wps/ui/GeneralHeader'
import { FIRECALC_DOC_TITLE } from '@wps/utils/constants'
import FBATable from 'features/fbaCalculator/components/FBATable'
import type React from 'react'
import { useEffect } from 'react'
import Footer from '@/features/landingPage/components/Footer'

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
