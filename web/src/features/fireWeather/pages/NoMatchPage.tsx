import { makeStyles } from "@material-ui/core"
import { Container, PageHeader, PageTitle } from "components"
import React from "react"

const useStyles = makeStyles(theme => ({
    root: {
      background: theme.palette.info.light,
      borderBottomWidth: 2,
      borderBottomStyle: 'solid',
      borderBottomColor: theme.palette.secondary.main
    }
  }))

export const NoMatchPage: React.FunctionComponent = () => {
    const classes = useStyles()
  
    return (
        <main>
        <PageHeader title="Predictive Services Unit" productName="Predictive Services Unit"/>
        <Container>
          <h1>Page Not Found</h1>
          <p>If you enetered a web address please check it was correct.</p>
          <p>You can also reach out the the Predictive Services Unit via TEAMS or <a href="mailto:bcws.predictiveservices@gov.bc.ca">send us an email</a> to find the information you need.</p>
        </Container>
      </main>
    )
  }