""" Percentage conifer (PC), percentage dead fir (PDF), crown closure (CC), crown base height (CBH),
and crown fuel load (CFL) constants for each fuel type from CFFDRS. """
# TODO: Move these constants (as columns) into fuel_types table in our database once all CFL
# values have been confirmed.
#
# PC, PDF, CC, CDH from the Red Book. Assumes values of 1 CBH.
# CC: Assume values of None for non grass types, and 0 for O1A and O1B.
# CFL is based on Table 8, page 35, of "Development and Structure of the Canadian Forest Fire Behaviour
# Prediction System" from Forestry Canada Fire Danger Group, Information Report ST-X-3, 1992.
# For D1, D2, O1A, O1B, S1, S2 and S3 - a value of 1.0 is used.
# TODO: Establish correct method of calculating HFI for D1, D2, O1A, O1B, S1, S2 and S3
FUEL_TYPE_LOOKUP = {"C1": {"PC": 100, "PDF": 0, "CC": None, "CBH": 2, "CFL": 0.75},
                    "C2": {"PC": 100, "PDF": 0, "CC": None, "CBH": 3, "CFL": 0.8},
                    "C3": {"PC": 100, "PDF": 0, "CC": None, "CBH": 8, "CFL": 1.15},
                    "C4": {"PC": 100, "PDF": 0, "CC": None, "CBH": 4, "CFL": 1.2},
                    "C5": {"PC": 100, "PDF": 0, "CC": None, "CBH": 18, "CFL": 1.2},
                    "C6_2": {"PC": 100, "PDF": 0, "CC": None, "CBH": 2, "CFL": 1.8},
                    "C6_7": {"PC": 100, "PDF": 0, "CC": None, "CBH": 7, "CFL": 1.8},
                    "C7": {"PC": 100, "PDF": 0, "CC": None, "CBH": 10, "CFL": 0.5},
                    # No CBH listed in RB fire intensity class table for D1.
                    # Using default CBH value of 3, as specified in fbp.Rd in cffdrs R package.
                    "D1": {"PC": 0, "PDF": 0, "CC": None, "CBH": 3, "CFL": 1.0},  # TODO: check cfl
                    # No CBH listed in RB fire intensity class table for D2.
                    # Using default CBH value of 3, as specified in fbp.Rd in cffdrs R package.
                    "D2": {"PC": 0, "PDF": 0, "CC": None, "CBH": 3, "CFL": 1.0},  # TODO: check cfl
                    "M1_25C": {"PC": 25, "PDF": 0, "CC": None, "CBH": 6, "CFL": 0.8},
                    "M1_50C": {"PC": 50, "PDF": 0, "CC": None, "CBH": 6, "CFL": 0.8},
                    "M1_75C": {"PC": 75, "PDF": 0, "CC": None, "CBH": 6, "CFL": 0.8},
                    "M2_25C": {"PC": 25, "PDF": 0, "CC": None, "CBH": 6, "CFL": 0.8},
                    "M2_50C": {"PC": 50, "PDF": 0, "CC": None, "CBH": 6, "CFL": 0.8},
                    "M2_75C": {"PC": 75, "PDF": 0, "CC": None, "CBH": 6, "CFL": 0.8},
                    "M3_30D": {"PC": 0, "PDF": 30, "CC": None, "CBH": 6, "CFL": 0.8},
                    "M3_60D": {"PC": 0, "PDF": 60, "CC": None, "CBH": 6, "CFL": 0.8},
                    "M3_100D": {"PC": 0, "PDF": 100, "CC": None, "CBH": 6, "CFL": 0.8},
                    "M4_30D": {"PC": 0, "PDF": 30, "CC": None, "CBH": 6, "CFL": 0.8},
                    "M4_60D": {"PC": 0, "PDF": 60, "CC": None, "CBH": 6, "CFL": 0.8},
                    "M4_100D": {"PC": 0, "PDF": 100, "CC": None, "CBH": 6, "CFL": 0.8},
                    # NOTE! I think having a default CC of 0 is dangerous, I think we should rather just
                    # fail to calculate ROS, and say, unknown.
                    "O1A": {"PC": 0, "PDF": 0, "CC": 0, "CBH": 1, "CFL": 1.0},  # TODO: check cfl
                    "O1B": {"PC": 0, "PDF": 0, "CC": 0, "CBH": 1, "CFL": 1.0},  # TODO: check cfl
                    "S1": {"PC": 0, "PDF": 0, "CC": None, "CBH": 1, "CFL": 1.0},  # TODO: check cfl
                    "S2": {"PC": 0, "PDF": 0, "CC": None, "CBH": 1, "CFL": 1.0},  # TODO: check cfl
                    "S3": {"PC": 0, "PDF": 0, "CC": None, "CBH": 1, "CFL": 1.0}  # TODO: check cfl
                    }
