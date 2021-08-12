""" Percentage conifer (PC), percentage dead fir (PDF), crown closure (CC), crown base height (CBH),
and crown fuel load (CFL) constants for each fuel type from CFFDRS. """
from app.schemas.fba_calc import FuelTypeEnum

# TODO: Move these constants (as columns) into fuel_types table in our database once all CFL
# values have been confirmed.
#
# PC, PDF, CC, CDH from the Red Book. Assumes values of 1 CBH.
# CC: Assume values of None for non grass types, and 0 for O1A and O1B.
# CFL is based on Table 8, page 35, of "Development and Structure of the Canadian Forest Fire Behaviour
# Prediction System" from Forestry Canada Fire Danger Group, Information Report ST-X-3, 1992.
# For D1, D2, O1A, O1B, S1, S2 and S3 - a value of 1.0 is used.
# TODO: Establish correct method of calculating HFI for D1, D2, O1A, O1B, S1, S2 and S3
# NOTE: For any given fuel types, there are a large number of possible permutations, e.g.
#   M3 can have some range 0 to 100% of dead fir in it. These values merely represent the most commen
#   default set of configurations we're likely to encounter.
FUEL_TYPE_DEFAULTS = {
    FuelTypeEnum.C1: {"PC": 100, "PDF": 0, "CC": None, "CBH": 2, "CFL": 0.75},
    FuelTypeEnum.C2: {"PC": 100, "PDF": 0, "CC": None, "CBH": 3, "CFL": 0.8},
    FuelTypeEnum.C3: {"PC": 100, "PDF": 0, "CC": None, "CBH": 8, "CFL": 1.15},
    FuelTypeEnum.C4: {"PC": 100, "PDF": 0, "CC": None, "CBH": 4, "CFL": 1.2},
    FuelTypeEnum.C5: {"PC": 100, "PDF": 0, "CC": None, "CBH": 18, "CFL": 1.2},
    FuelTypeEnum.C6: {"PC": 100, "PDF": 0, "CC": None, "CBH": 7, "CFL": 1.8},
    FuelTypeEnum.C7: {"PC": 100, "PDF": 0, "CC": None, "CBH": 10, "CFL": 0.5},
    # No CBH listed in RB fire intensity class table for D1.
    # Using default CBH value of 3, as specified in fbp.Rd in cffdrs R package.
    FuelTypeEnum.D1: {"PC": 0, "PDF": 0, "CC": None, "CBH": 3, "CFL": 1.0},  # TODO: check cfl
    # No CBH listed in RB fire intensity class table for D2.
    # Using default CBH value of 3, as specified in fbp.Rd in cffdrs R package.
    FuelTypeEnum.D2: {"PC": 0, "PDF": 0, "CC": None, "CBH": 3, "CFL": 1.0},  # TODO: check cfl
    FuelTypeEnum.M1: {"PC": 50, "PDF": 0, "CC": None, "CBH": 6, "CFL": 0.8},
    FuelTypeEnum.M2: {"PC": 50, "PDF": 0, "CC": None, "CBH": 6, "CFL": 0.8},
    FuelTypeEnum.M3: {"PC": 0, "PDF": 30, "CC": None, "CBH": 6, "CFL": 0.8},
    FuelTypeEnum.M4: {"PC": 0, "PDF": 30, "CC": None, "CBH": 6, "CFL": 0.8},
    # NOTE! I think having a default CC of 0 is dangerous, I think we should rather just
    # fail to calculate ROS, and say, unknown.
    FuelTypeEnum.O1A: {"PC": 0, "PDF": 0, "CC": 0, "CBH": 1, "CFL": 1.0},  # TODO: check cfl
    FuelTypeEnum.O1B: {"PC": 0, "PDF": 0, "CC": 0, "CBH": 1, "CFL": 1.0},  # TODO: check cfl
    FuelTypeEnum.S1: {"PC": 0, "PDF": 0, "CC": None, "CBH": 1, "CFL": 1.0},  # TODO: check cfl
    FuelTypeEnum.S2: {"PC": 0, "PDF": 0, "CC": None, "CBH": 1, "CFL": 1.0},  # TODO: check cfl
    FuelTypeEnum.S3: {"PC": 0, "PDF": 0, "CC": None, "CBH": 1, "CFL": 1.0}  # TODO: check cfl
}
