import React from 'react'
import makeStyles from '@mui/styles/makeStyles'
import ContentContainer from 'app/ContentContainer'
import Footer from 'landingPage/Footer'
import Search from 'landingPage/Search'
import Sidebar from 'landingPage/Sidebar'
import { FOOTER_HEIGHT } from 'utils/constants'
import ToolCards from 'landingPage/ToolCards'

const useStyles = makeStyles(() => ({
  content: {
    display: 'flex',
    flexGrow: 1
  },
  root: {
    display: 'flex',
    flexDirection: 'column',
    margin: 0,
    minHeight: '100vh'
  },
  subcontainer: {
    display: 'flex',
    flexDirection: 'column',
    flexGrow: 1
  },
  sidebar: {
    display: 'flex',
    flexDirection: 'column',
    maxHeight: `calc(100vh - ${FOOTER_HEIGHT}px)`,
    overflowY: 'auto',
    minWidth: '251px',
    width: '251px'
  }
}))

const LandingPage: React.FunctionComponent = () => {
  const classes = useStyles()

  return (
    <div className={classes.root}>
      <div className={classes.content}>
        <div className={classes.sidebar}>
          <Sidebar />
        </div>
        <div className={classes.subcontainer}>
          <Search />
          <ContentContainer>
            {/* Future home of a routing component */}
            <ToolCards />
          </ContentContainer>
        </div>
      </div>
      <Footer />
    </div>
  )
}

export default LandingPage
