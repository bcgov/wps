import React, { useEffect } from 'react'
import { useTheme } from '@mui/material/styles'
import useMediaQuery from '@mui/material/useMediaQuery'
import makeStyles from '@mui/styles/makeStyles'
import ContentContainer from 'app/ContentContainer'
import Footer from 'features/landingPage/components/Footer'
import Sidebar from 'features/landingPage/components/Sidebar'
import ToolCards from 'features/landingPage/components/ToolCards'
import { LANDING_PAGE_DOC_TITLE } from 'utils/constants'

const useStyles = makeStyles(theme => ({
  content: {
    display: 'flex',
    flexGrow: 1
  },
  root: {
    display: 'flex',
    flexDirection: 'column',
    minHeight: '100vh'
  },
  subcontainer: {
    display: 'flex',
    flexDirection: 'column',
    flexGrow: 1
  },
  sidebar: {
    display: 'flex',
    flexGrow: 1,
    overflowY: 'auto',
    [theme.breakpoints.up('sm')]: {
      minWidth: '251px',
      maxWidth: '251px',
      width: '251px'
    }
  }
}))

const LandingPage: React.FunctionComponent = () => {
  const theme = useTheme()
  const classes = useStyles()
  const isSmall = useMediaQuery(theme.breakpoints.down('sm'))

  useEffect(() => {
    document.title = LANDING_PAGE_DOC_TITLE
  }, [])

  return (
    <div className={classes.root}>
      <div className={classes.content}>
        <div className={classes.sidebar}>
          <Sidebar />
        </div>
        {!isSmall && (
          <div className={classes.subcontainer}>
            <ContentContainer>
              {/* Future home of a routing component once we integrate apps into the landing page
               *For now the landing page just displays the side bar and tool cards
               */}
              <ToolCards />
            </ContentContainer>
          </div>
        )}
      </div>
      <Footer />
    </div>
  )
}

export default LandingPage
