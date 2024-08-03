import { Box, Tabs, Tab, Grid, TextField } from '@mui/material'
import { FireShape } from 'api/fbaAPI'
import InfoAccordion from 'features/fba/components/infoPanel/InfoAccordion'
import { DateTime } from 'luxon'
import React, {useEffect, useState} from 'react'

interface AdvisoryReportProps {    
    issueDate: DateTime | null
    forDate: DateTime
    // selectedFireZoneUnit: FireShape | undefined
}

interface TabPanelProps {
    children?: React.ReactNode
    index: number
    value: number
}

const TabPanel = ({children, index, value}: TabPanelProps) => {
    return (
        <div
            hidden={value !== index}
            id={`tabpanel-${index}`}
        >
            {value === index && (
                <Box paddingBottom={3}>{children}</Box>
            )}
        </div>
    )
}

const composeAdvisoryText = (issueDate: DateTime | null, forDate: DateTime) => {
    if (issueDate?.isValid){
        return `Issued on ${issueDate.toISODate()} for ${forDate.toISODate()}
    `}
    else {
        return `No advisories issued for today`
    }
}

const AdvisoryReport = ({issueDate, forDate}: AdvisoryReportProps) => {
    const [value, setValue] = useState(0)

    const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
        setValue(newValue);
      }

    return (
        <div data-testid="advisory-report">
          <InfoAccordion
            defaultExpanded={true}
            title={'Advisory Report'}
          >
            <Grid container justifyContent="center">
                <Grid item sx={{ width: '90%'}}>
                    <Box>
                        <Tabs value={value} onChange={handleTabChange}>
                            <Tab label='BULLETIN'/>
                        </Tabs>
                    </Box>
                    <TabPanel value={value} index={0}>
                        <TextField 
                            fullWidth
                            multiline
                            variant='outlined' 
                            value={composeAdvisoryText(issueDate, forDate)}
                            minRows={10}
                            maxRows={50}
                            InputProps={{
                                readOnly: true,
                              }}
                        />
                    </TabPanel>
                </Grid>
            </Grid>
          </InfoAccordion>
        </div>
      )
    }
    
export default AdvisoryReport