interface ASAAboutDataProps {
  advisoryThreshold: number
}

export const ASAAboutDataContent = ({ advisoryThreshold }: ASAAboutDataProps) => (
  <ul style={{ margin: 0 }}>
    <li>
      A Fire Zone is under a Fire Behaviour Advisory if greater than {advisoryThreshold}% of the combustible land
      (trees, grass, slash) is forecast to have a Head Fire Intensity between 4,000 and 10,000 kW/m.
    </li>
    <br />
    <li>
      A Fire Zone is under a Fire Behaviour Warning if greater than {advisoryThreshold}% of the combustible land is
      forecast to have a Head Fire Intensity greater than 10,000 kW/m.
    </li>
    <br />
    <li>
      The{' '}
      <a href="https://cwfis.cfs.nrcan.gc.ca/background/fueltypes/c1" target="_blank" rel="noopener noreferrer">
        fuel types
      </a>{' '}
      chosen for the text bulletin are the most common fuel types in a zone that meet or exceed the Fire Behaviour
      Advisory threshold of 4,000 kW/m.
    </li>
  </ul>
)
