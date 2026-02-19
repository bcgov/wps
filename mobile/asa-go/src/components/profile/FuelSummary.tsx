import { useMemo } from "react";
import { FireShape, FireZoneFuelStats } from "api/fbaAPI";
import { Box, Typography } from "@mui/material";
import { groupBy } from "lodash";
import {
  DataGridPro,
  GridColDef,
  GridColumnHeaderParams,
  GridRenderCellParams,
} from "@mui/x-data-grid-pro";
import { styled } from "@mui/material/styles";
import CriticalHours from "@/components/profile/CriticalHours";
import FuelDistribution from "@/components/profile/FuelDistribution";

export interface FuelTypeInfoSummary {
  area: number;
  criticalHoursStart?: number;
  criticalHoursEnd?: number;
  id: number;
  code: string;
  description: string;
  percent?: number;
  selected: boolean;
}

interface FuelSummaryProps {
  fireZoneFuelStats: Record<number, FireZoneFuelStats[]>;
  selectedFireZoneUnit: FireShape | undefined;
}

const StyledHeader = styled("div")(({ theme }) => ({
  whiteSpace: "normal",
  wordWrap: "break-word",
  textAlign: "left",
  fontSize: "14px",
  fontWeight: "700",
  color: theme.palette.primary.main,
}));

// Column definitions for fire zone unit fuel summary table
const columns: GridColDef[] = [
  {
    field: "code",
    headerClassName: "fuel-summary-header",
    headerName: "Fuel Type",
    sortable: false,
    minWidth: 120,
    renderHeader: (params: GridColumnHeaderParams) => (
      <StyledHeader>{params.colDef.headerName}</StyledHeader>
    ),
    renderCell: (params: GridRenderCellParams) => (
      <Typography
        sx={{
          fontSize: "0.75rem",
          display: "flex",
          fontWeight: "bold",
          whiteSpace: "normal",
          wordBreak: "break-word",
        }}
      >
        {params.row[params.field]}
      </Typography>
    ),
  },
  {
    field: "area",
    flex: 1,
    headerClassName: "fuel-summary-header",
    headerName: "% Under Advisory",
    sortable: false,
    renderHeader: (params: GridColumnHeaderParams) => (
      <StyledHeader>{params.colDef.headerName}</StyledHeader>
    ),
    renderCell: (params: GridRenderCellParams) => {
      return (
        <FuelDistribution
          code={params.row["code"]}
          percent={params.row["percent"]}
        />
      );
    },
  },
  {
    field: "criticalHours",
    headerClassName: "fuel-summary-header",
    headerName: "Critical Hours",
    minWidth: 110,
    sortable: false,
    renderHeader: (params: GridColumnHeaderParams) => (
      <StyledHeader>{params.colDef.headerName}</StyledHeader>
    ),
    renderCell: (params: GridRenderCellParams) => {
      return (
        <CriticalHours
          start={params.row["criticalHoursStart"]}
          end={params.row["criticalHoursEnd"]}
        />
      );
    },
  },
];

const FuelSummary = ({
  fireZoneFuelStats,
  selectedFireZoneUnit,
}: FuelSummaryProps) => {
  const fuelTypeInfoRollup = useMemo<FuelTypeInfoSummary[]>(() => {
    if (!fireZoneFuelStats || !selectedFireZoneUnit) {
      return [];
    }

    const shapeId = selectedFireZoneUnit.fire_shape_id;
    const fuelDetails = fireZoneFuelStats[shapeId];

    if (!fuelDetails) return [];

    const rollUp: FuelTypeInfoSummary[] = [];

    const groupedFuelDetails = groupBy(fuelDetails, "fuel_type.fuel_type_id");

    for (const key in groupedFuelDetails) {
      const groupedFuelDetail = groupedFuelDetails[key];
      if (groupedFuelDetail.length) {
        const area = groupedFuelDetail.reduce((acc, { area }) => acc + area, 0);

        const fuelType = groupedFuelDetail[0].fuel_type;
        const startTime =
          groupedFuelDetail[0].critical_hours.start_time ?? undefined;
        const endTime =
          groupedFuelDetail[0].critical_hours.end_time ?? undefined;
        const fuel_area = groupedFuelDetail[0].fuel_area;

        rollUp.push({
          area,
          code: fuelType.fuel_type_code,
          description: fuelType.description,
          criticalHoursStart: startTime,
          criticalHoursEnd: endTime,
          id: fuelType.fuel_type_id,
          percent: fuel_area ? (area / fuel_area) * 100 : 0,
          selected: false,
        });
      }
    }

    return rollUp;
  }, [fireZoneFuelStats, selectedFireZoneUnit]);

  return (
    <Box>
      {fuelTypeInfoRollup.length === 0 ? (
        <Typography>No fuel type information available.</Typography>
      ) : (
        <DataGridPro
          columns={columns}
          density="compact"
          disableColumnMenu
          disableChildrenSorting
          disableColumnResize
          disableRowSelectionOnClick
          hideFooter={true}
          initialState={{
            sorting: {
              sortModel: [{ field: "area", sort: "desc" }],
            },
          }}
          rows={fuelTypeInfoRollup}
          showCellVerticalBorder
          showColumnVerticalBorder
          sx={{
            backgroundColor: "white",
            overflow: "hidden",
            "& .MuiDataGrid-sortIcon": {
              display: "none",
            },
            "& .MuiDataGrid-cell": {
              display: "flex",
              alignItems: "center",
            },
          }}
        ></DataGridPro>
      )}
    </Box>
  );
};

export default FuelSummary;
