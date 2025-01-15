import {
  MapView,
  VectorSource,
  FillLayer,
  LineLayer,
  SymbolLayer,
  Camera,
} from "@maplibre/maplibre-react-native";

export default function Page() {
  return (
    <MapView style={{ flex: 1 }} zoomEnabled compassEnabled>
      <Camera centerCoordinate={[-125, 54.5]} zoomLevel={3.5} />
      <VectorSource
        id="fireCentreSource"
        url="pmtiles://https://nrs.objectstore.gov.bc.ca/lwzrin/psu/pmtiles/fireCentres.pmtiles"
      >
        <LineLayer
          id="border-fire-centres"
          sourceLayerID="tippecanoe_input"
          style={{ lineColor: "red" }}
        />
      </VectorSource>
      <VectorSource
        id="fireZonesSource"
        url="pmtiles://https://nrs.objectstore.gov.bc.ca/lwzrin/psu/pmtiles/fireZoneUnits.pmtiles"
      >
        <LineLayer
          id="border-fire-zones"
          sourceLayerID="bc_bndy_fire_zone_units_4326"
          style={{ lineColor: "black" }}
        />
      </VectorSource>
    </MapView>
  );
}
