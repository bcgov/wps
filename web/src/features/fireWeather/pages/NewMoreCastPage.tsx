import React, { useEffect } from 'react'
import { makeStyles } from '@material-ui/core/styles'

import { PageHeader } from 'components'

const useStyles = makeStyles(theme => ({
  nav: {
    background: theme.palette.primary.light,
    color: theme.palette.primary.contrastText,
    minHeight: 60,
    fontSize: '1.3rem',
    display: 'flex',
    alignItems: 'center',
    paddingLeft: 25,
    paddingRight: 25
  },
  content: {
    display: 'flex'
  }
}))

const MoreCastPage = () => {
  const classes = useStyles()

  return (
    <main>
      <PageHeader
        title="Predictive Services Unit"
        productName="MoreCast"
        noContainer
        padding={25}
      />
      <div className={classes.nav}>MoreCast</div>
    </main>
  )
}

export default React.memo(MoreCastPage)
