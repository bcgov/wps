import { Container, PageHeader } from "components"
import React from "react"

export const NoMatchPage: React.FunctionComponent = () => {  
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