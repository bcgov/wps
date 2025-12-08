import { FireCenter, FireShape } from "@/api/fbaAPI";
import { useFireCentreDetails } from "@/hooks/useFireCentreDetails";
import { calculateStatusColour } from "@/utils/calculateZoneStatus";
import { Tab, Tabs } from "@mui/material";
import { Box } from "@mui/system";
import { isEmpty } from "lodash";
import { DateTime } from "luxon";
import { useEffect, useCallback, useMemo } from "react";

export interface FireZoneUnitTabsProps {
  selectedFireCenter: FireCenter | undefined;
  selectedFireZoneUnit: FireShape | undefined;
  setSelectedFireZoneUnit: React.Dispatch<
    React.SetStateAction<FireShape | undefined>
  >;
  children: React.ReactNode;
  date: DateTime;
}

const FireZoneUnitTabs = ({
  children,
  selectedFireCenter,
  selectedFireZoneUnit,
  setSelectedFireZoneUnit,
  date,
}: FireZoneUnitTabsProps) => {
  const sortedGroupedFireZoneUnits = useFireCentreDetails(
    selectedFireCenter,
    date
  );

  const getTabFireShape = useCallback(
    (tabNumber: number): FireShape | undefined => {
      if (sortedGroupedFireZoneUnits.length > 0) {
        const selectedTabZone = sortedGroupedFireZoneUnits[tabNumber];

        const fireShape: FireShape = {
          fire_shape_id: selectedTabZone.fire_shape_id,
          mof_fire_centre_name: selectedTabZone.fire_centre_name,
          mof_fire_zone_name: selectedTabZone.fire_shape_name,
        };

        return fireShape;
      }
    },
    [sortedGroupedFireZoneUnits]
  );

  const tabNumber = useMemo(() => {
    if (!selectedFireZoneUnit) return 0;

    const idx = sortedGroupedFireZoneUnits.findIndex(
      (zone) => zone.fire_shape_id === selectedFireZoneUnit.fire_shape_id
    );

    return idx >= 0 ? idx : 0;
  }, [selectedFireZoneUnit, sortedGroupedFireZoneUnits]);

  useEffect(() => {
    if (!selectedFireZoneUnit) {
      setSelectedFireZoneUnit(getTabFireShape(0));
    }
  }, [getTabFireShape, selectedFireZoneUnit, setSelectedFireZoneUnit]);

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
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
                  backgroundColor: calculateStatusColour(zone, "#FFFFFF"),
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
