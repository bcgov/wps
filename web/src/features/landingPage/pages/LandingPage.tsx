import React, { useEffect } from 'react'
import { styled } from '@mui/material/styles'
import { useTheme } from '@mui/material/styles'
import { theme } from 'app/theme'
import useMediaQuery from '@mui/material/useMediaQuery'
import ContentContainer from 'app/ContentContainer'
import Footer from 'features/landingPage/components/Footer'
import Sidebar from 'features/landingPage/components/Sidebar'
import ToolCards from 'features/landingPage/components/ToolCards'
import { LANDING_PAGE_DOC_TITLE } from 'utils/constants'

const PREFIX = 'LandingPage'

const Root = styled('div', {
  name: `${PREFIX}-root`
})({
  display: 'flex',
  flexDirection: 'column',
  minHeight: '100vh'
})

const Content = styled('div', {
  name: `${PREFIX}-content`
})({
  display: 'flex',
  flexGrow: 1
})

const SubContainer = styled('div', {
  name: `${PREFIX}-subContainer`
})({
  display: 'flex',
  flexDirection: 'column',
  flexGrow: 1
})

const SidebarContainer = styled('div', {
  name: `${PREFIX}-sidebarContainer`
})({
  display: 'flex',
  flexGrow: 1,
  overflowY: 'auto',
  [theme.breakpoints.up('sm')]: {
    minWidth: '260px',
    maxWidth: '264px',
    width: '251px'
  }
})

const LandingPage: React.FunctionComponent = () => {
  const theme = useTheme()

  const isSmall = useMediaQuery(theme.breakpoints.down('sm'))

  useEffect(() => {
    document.title = LANDING_PAGE_DOC_TITLE
  }, [])

  return (
    <Root>
      <Content>
        <SidebarContainer>
          <Sidebar />
        </SidebarContainer>
        {!isSmall && (
          <SubContainer>
            <ContentContainer>
              {/* Future home of a routing component once we integrate apps into the landing page
               *For now the landing page just displays the side bar and tool cards
               */}
              <ToolCards />
            </ContentContainer>
          </SubContainer>
        )}
      </Content>
      <Footer />
    </Root>
  )
}

export default LandingPage
