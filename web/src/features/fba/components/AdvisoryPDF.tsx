import React from 'react'
import { Document, Page, Text, View, StyleSheet } from '@react-pdf/renderer'

const styles = StyleSheet.create({
  page: {
    flexDirection: 'row'
  },
  section: {
    margin: 10,
    padding: 10,
    flexGrow: 1
  },
  subtitle: {
    fontSize: 18,
    margin: 12
  }
})

const AdvisoryPDF = () => {
  return (
    <Document>
      <Page size="A4" style={styles.page}>
        <View style={styles.section}>
          <Text style={styles.subtitle} break>
            Section 1
          </Text>
          <Text>
            {' '}
            The advisory is for C3, C7, and slash fuel types for the whole fire centre
            except the Bowron Lake Chain area and East of Quesnel Lake. • From 13:00-20:00
            there is potential for intermittent crown fire when winds exceed 10 km/hr, and
            crown fires from 13:00-21:00 when winds exceed 10 km/h. • There is potential
            for Crown Fire from Anahim Lake to Riske Creek, Meadow Lake to Young Lake, and
            Horsefly from 16:00-19:00 when winds exceed 15 km/hr. • For slash fuel types
            there is potential for fire intensity to exceed 10,000 kw/m throughout the
            day, with rates of spread up to 20 m/min. • This is a result of dry fuels,
            high temperatures, and low RH values.
          </Text>
        </View>
        <View style={styles.section} break>
          <Text style={styles.subtitle} break>
            Section 2
          </Text>
          <Text>
            The advisory is for C3, C7, and slash fuel types for the whole fire centre
            except the Bowron Lake Chain area and East of Quesnel Lake. • From 13:00-20:00
            there is potential for intermittent crown fire when winds exceed 10 km/hr, and
            crown fires from 13:00-21:00 when winds exceed 10 km/h. • There is potential
            for Crown Fire from Anahim Lake to Riske Creek, Meadow Lake to Young Lake, and
            Horsefly from 16:00-19:00 when winds exceed 15 km/hr. • For slash fuel types
            there is potential for fire intensity to exceed 10,000 kw/m throughout the
            day, with rates of spread up to 20 m/min. • This is a result of dry fuels,
            high temperatures, and low RH values.
          </Text>
        </View>
      </Page>
      <Page style={styles.page}>
        <Text>insert map here</Text>
      </Page>
    </Document>
  )
}

export default React.memo(AdvisoryPDF)
