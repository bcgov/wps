import { Map, View } from "ol";
import "ol/ol.css";
import { fromLonLat } from "ol/proj";
import { boundingExtent } from "ol/extent";
import ScaleLine from "ol/control/ScaleLine";
import VectorTileLayer from "ol/layer/VectorTile";
import React, { useEffect, useRef, useState } from "react";
import { BC_EXTENT } from "utils/constants";
import { FireCenter, FireShape, FireShapeArea, RunType } from "api/fbaAPI";
import {
  fireCentreLabelStyler,
  fireShapeLabelStyler,
  fireCentreLineStyler,
  hfiStyler,
  fireShapeLineStyler,
} from "@/featureStylers";
import { DateTime } from "luxon";
import { cloneDeep, isNull, isUndefined } from "lodash";
import { Box } from "@mui/material";
import ScalebarContainer from "@/components/ScaleBarContainer";
import { fireZoneExtentsMap } from "@/fireZoneUnitExtents";
import { CENTER_OF_BC } from "@/utils/constants";
import { extentsMap } from "@/fireCentreExtents";
import { PMTilesFileVectorSource } from "@/utils/pmtilesVectorSource";
import { PMTilesCache } from "@/utils/pmtilesCache";
import { Filesystem } from "@capacitor/filesystem";
import {
  createBasemapLayer,
  createLocalBasemapVectorLayer,
  LOCAL_BASEMAP_LAYER_NAME,
} from "@/layerDefinitions";
import TileLayer from "ol/layer/Tile";
import { useSelector } from "react-redux";
import { selectNetworkStatus } from "@/store";
import TodayTomorrowSwitch from "@/components/TodayTomorrowSwitch";
export const MapContext = React.createContext<Map | null>(null);

const bcExtent = boundingExtent(BC_EXTENT.map((coord) => fromLonLat(coord)));

export interface FBAMapProps {
  testId?: string;
  dateOfInterest: DateTime;
  setDateOfInterest: React.Dispatch<React.SetStateAction<DateTime>>;
  selectedFireCenter: FireCenter | undefined;
  selectedFireShape: FireShape | undefined;
  fireShapeAreas: FireShapeArea[];
  advisoryThreshold: number;
  zoomSource?: "fireCenter" | "fireShape";
}

const FBAMap = (props: FBAMapProps) => {
  const [map, setMap] = useState<Map | null>(null);
  const [basemapLayer] = useState<TileLayer>(createBasemapLayer());
  const [localBasemapVectorLayer, setLocalBasemapVectorLayer] =
    useState<VectorTileLayer>(() => {
      const layer = new VectorTileLayer();
      layer.set("name", LOCAL_BASEMAP_LAYER_NAME);
      return layer;
    });
  const { networkStatus } = useSelector(selectNetworkStatus);
  const mapRef = useRef<HTMLDivElement | null>(
    null
  ) as React.MutableRefObject<HTMLElement>;
  const scaleRef = useRef<HTMLDivElement | null>(
    null
  ) as React.MutableRefObject<HTMLElement>;

  const removeLayerByName = (map: Map, layerName: string) => {
    const layer = map
      .getLayers()
      .getArray()
      .find((l) => l.getProperties()?.name === layerName);
    if (layer) {
      map.removeLayer(layer);
    }
  };

  useEffect(() => {
    // zoom to fire center or whole province
    if (!map) return;

    if (props.selectedFireCenter && props.zoomSource === "fireCenter") {
      const fireCentreExtent = extentsMap.get(props.selectedFireCenter.name);
      if (fireCentreExtent) {
        map.getView().fit(fireCentreExtent.extent, {
          duration: 400,
          padding: [50, 50, 50, 50],
        });
      }
    } else if (!props.selectedFireCenter) {
      // reset map view to full province
      map.getView().fit(bcExtent, { duration: 600, padding: [50, 50, 50, 50] });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [props.selectedFireCenter]);

  useEffect(() => {
    // zoom to fire zone
    if (!map) return;

    if (props.selectedFireShape && props.zoomSource === "fireShape") {
      const zoneExtent = fireZoneExtentsMap.get(
        props.selectedFireShape.fire_shape_id.toString()
      );
      if (!isUndefined(zoneExtent)) {
        map.getView().fit(zoneExtent, {
          duration: 400,
          padding: [100, 100, 100, 100],
          maxZoom: 8,
        });
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [props.selectedFireShape]);

  useEffect(() => {
    if (!map) return;

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    props.selectedFireCenter,
    props.selectedFireShape,
    props.fireShapeAreas,
    props.advisoryThreshold,
  ]);

  useEffect(() => {
    // Toggle basemap visibility based on network connection status.
    if (networkStatus.connected === true) {
      localBasemapVectorLayer.setVisible(false);
      basemapLayer.setVisible(true);
    } else {
      basemapLayer.setVisible(false);
      localBasemapVectorLayer.setVisible(true);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [networkStatus]);

  useEffect(() => {
    // The locally cached basemap pmtiles layer loads async, so add it
    // to the map once it is loaded and state updated.
    if (isNull(map) || isNull(localBasemapVectorLayer)) {
      return;
    }
    if (networkStatus.connected) {
      localBasemapVectorLayer.setVisible(false);
    }
    // Remove the placeholder VTL and then add the new localBasemapVectorLayer
    removeLayerByName(map, LOCAL_BASEMAP_LAYER_NAME);
    map.addLayer(localBasemapVectorLayer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [localBasemapVectorLayer]);

  useEffect(() => {
    // The React ref is used to attach to the div rendered in our
    // return statement of which this map's target is set to.
    // The ref is a div of type  HTMLDivElement.

    // Pattern copied from web/src/features/map/Map.tsx
    if (!mapRef.current) return;

    // Create the map with the options above and set the target
    // To the ref above so that it is rendered in that div
    const mapObject = new Map({
      view: new View({
        zoom: 5,
        center: fromLonLat(CENTER_OF_BC),
      }),
      layers: [],
      overlays: [],
    });
    mapObject.setTarget(mapRef.current);

    const scaleBar = new ScaleLine({
      bar: true,
      minWidth: 160,
      steps: 4,
    });
    scaleBar.setTarget(scaleRef.current);
    scaleBar.setMap(mapObject);

    mapObject.getView().fit(bcExtent, { padding: [50, 50, 50, 50] });

    setMap(mapObject);

    const loadPMTiles = async () => {
      // TODO make for date, run type, run date configurable from UI
      const hfiVectorSource = await PMTilesFileVectorSource.createHFILayer(
        new PMTilesCache(Filesystem),
        {
          filename: "hfi.pmtiles",
          for_date: DateTime.fromFormat("2024/08/08", "yyyy/MM/dd"),
          run_type: RunType.FORECAST,
          run_date: DateTime.fromFormat("2024/08/08", "yyyy/MM/dd"),
        }
      );

      const fireCentresSource = await PMTilesFileVectorSource.createStaticLayer(
        new PMTilesCache(Filesystem),
        {
          filename: "fireCentres.pmtiles",
        }
      );

      const fireCentreLabelVectorSource =
        await PMTilesFileVectorSource.createStaticLayer(
          new PMTilesCache(Filesystem),
          {
            filename: "fireCentreLabels.pmtiles",
          }
        );

      const fireZoneSource = await PMTilesFileVectorSource.createStaticLayer(
        new PMTilesCache(Filesystem),
        {
          filename: "fireZoneUnits.pmtiles",
        }
      );

      const fireZoneLabelVectorSource =
        await PMTilesFileVectorSource.createStaticLayer(
          new PMTilesCache(Filesystem),
          {
            filename: "fireZoneUnitLabels.pmtiles",
          }
        );
      if (mapObject) {
        const fireCentreFileLayer = new VectorTileLayer({
          source: fireCentresSource,
          style: fireCentreLineStyler(props.selectedFireCenter),
          zIndex: 52,
        });

        const fireCentreLabelsFileLayer = new VectorTileLayer({
          source: fireCentreLabelVectorSource,
          style: fireCentreLabelStyler,
          zIndex: 100,
          maxZoom: 6,
        });

        const fireZoneFileLayer = new VectorTileLayer({
          source: fireZoneSource,
          style: fireShapeLineStyler(
            cloneDeep(props.fireShapeAreas),
            props.advisoryThreshold,
            props.selectedFireShape
          ),
          zIndex: 53,
          properties: { name: "fireShapeVector" },
        });

        const fireZoneLabelFileLayer = new VectorTileLayer({
          source: fireZoneLabelVectorSource,
          declutter: true,
          style: fireShapeLabelStyler(props.selectedFireShape),
          zIndex: 99,
          minZoom: 6,
        });

        const hfiFileLayer = new VectorTileLayer({
          source: hfiVectorSource,
          style: hfiStyler,
          zIndex: 52,
        });

        const localBasemapLayer = await createLocalBasemapVectorLayer();
        setLocalBasemapVectorLayer(localBasemapLayer);

        mapObject.addLayer(basemapLayer);
        mapObject.addLayer(hfiFileLayer);
        mapObject.addLayer(fireCentreFileLayer);
        mapObject.addLayer(fireCentreLabelsFileLayer);
        mapObject.addLayer(fireZoneFileLayer);
        mapObject.addLayer(fireZoneLabelFileLayer);
      }
    };
    loadPMTiles();
    return () => {
      mapObject.setTarget("");
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <MapContext.Provider value={map}>
      <Box
        ref={mapRef}
        data-testid="fba-map"
        sx={{
          display: "flex",
          flex: 1,
          position: "relative",
        }}
      >
        <Box
          sx={{ position: "absolute", left: "8px", bottom: "8px", zIndex: 1 }}
        >
          <TodayTomorrowSwitch
            date={props.dateOfInterest}
            setDate={props.setDateOfInterest}
          />
        </Box>
        <ScalebarContainer ref={scaleRef} />
      </Box>
    </MapContext.Provider>
  );
};

export default React.memo(FBAMap);
