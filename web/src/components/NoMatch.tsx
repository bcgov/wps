import { makeStyles } from "@material-ui/core"
import { Container, PageHeader, PageTitle } from "components"
import React from "react"

const useStyles = makeStyles(theme => ({
    root: {
      background: theme.palette.primary.main,
      borderBottomWidth: 2,
      borderBottomStyle: 'solid',
      borderBottomColor: theme.palette.secondary.main
    }
  }))

export const NoMatch: React.FunctionComponent = () => {
    const classes = useStyles()
  
    return (
        <main className={classes.root}>
        <PageHeader title="Not Found" productName="Not Found"/>
        <PageTitle title="Not Found" />
        <Container>
            <p>404 Not Found</p>
        </Container>
      </main>
    )
  }