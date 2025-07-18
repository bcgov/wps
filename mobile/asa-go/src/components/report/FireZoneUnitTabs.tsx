import { FireCenter, FireShape } from "@/api/fbaAPI";
import { useFireCentreDetails } from "@/hooks/useFireCentreDetails";
import { calculateStatusColour } from "@/utils/calculateZoneStatus";
import { Tab, Tabs } from "@mui/material";
import { Box } from "@mui/system";
import { isEmpty } from "lodash";
import { useEffect, useState } from "react";

interface FireZoneUnitTabsProps {
  advisoryThreshold: number;
  selectedFireCenter: FireCenter | undefined;
  selectedFireZoneUnit: FireShape | undefined;
  setSelectedFireZoneUnit: React.Dispatch<
    React.SetStateAction<FireShape | undefined>
  >;
  children: React.ReactNode;
}

const FireZoneUnitTabs = ({
  advisoryThreshold,
  children,
  selectedFireCenter,
  selectedFireZoneUnit,
  setSelectedFireZoneUnit,
}: FireZoneUnitTabsProps) => {
  const [tabNumber, setTabNumber] = useState(0);
  const sortedGroupedFireZoneUnits = useFireCentreDetails(selectedFireCenter);

  const getTabFireShape = (tabNumber: number): FireShape | undefined => {
    if (sortedGroupedFireZoneUnits.length > 0) {
      const selectedTabZone = sortedGroupedFireZoneUnits[tabNumber];

      const fireShape: FireShape = {
        fire_shape_id: selectedTabZone.fire_shape_id,
        mof_fire_centre_name: selectedTabZone.fire_centre_name,
        mof_fire_zone_name: selectedTabZone.fire_shape_name,
      };

      return fireShape;
    }
  };

  useEffect(() => {
    if (selectedFireZoneUnit) {
      const newIndex = sortedGroupedFireZoneUnits.findIndex(
        (zone) => zone.fire_shape_id === selectedFireZoneUnit.fire_shape_id
      );
      if (newIndex !== -1) {
        setTabNumber(newIndex);
      }
    } else {
      setTabNumber(0);
      setSelectedFireZoneUnit(getTabFireShape(0)); // if no selected FireShape, select the first one in the sorted tabs
    }
  }, [selectedFireZoneUnit, sortedGroupedFireZoneUnits]);

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setTabNumber(newValue);

    const fireShape = getTabFireShape(newValue);
    setSelectedFireZoneUnit(fireShape);
  };

  return (
    <Box
      id="fire-zone-unit-tabs"
      sx={{
        display: "flex",
        flexDirection: "column",
        width: "100%",
      }}
    >
      {!isEmpty(sortedGroupedFireZoneUnits) && (
        <Tabs
          value={tabNumber}
          onChange={handleTabChange}
          sx={{
            "& .MuiTab-root": {
              flex: 1,
              minWidth: 0,
            },
            ".MuiTabs-indicator": {
              height: "4px",
            },
          }}
        >
          {sortedGroupedFireZoneUnits.map((zone, index) => {
            const isActive = tabNumber === index;
            const key = zone.fire_shape_id;
            return (
              <Tab
                key={key}
                data-testid={`zone-${key}-tab`}
                sx={{
                  backgroundColor: calculateStatusColour(
                    zone.fireShapeDetails,
                    advisoryThreshold,
                    "#FFFFFF"
                  ),
                  fontWeight: "bold",
                  color: isActive ? "black" : "grey",
                  minHeight: "30px",
                }}
                label={zone.fire_shape_name.split("-")[0]}
                aria-label={`zone-${key}-tab`}
              />
            );
          })}
        </Tabs>
      )}
      {children}
    </Box>
  );
};

export default FireZoneUnitTabs;
