""" Defines standardized fire starts for the different fire centres """
from app.schemas.hfi_calc import FireCentreFireStarts, FireStartRange

# TODO: put in database once shape of FireStarts confirmed
lowest_fire_starts = FireStartRange(label='0-1', lookup_table={1: 1, 2: 1, 3: 2, 4: 3, 5: 4})
one_2_two_starts = FireStartRange(label='1-2', lookup_table={1: 1, 2: 2, 3: 3, 4: 4, 5: 5})
two_2_three_starts = FireStartRange(label='2-3', lookup_table={1: 2, 2: 3, 3: 4, 4: 5, 5: 6})
three_2_six_starts = FireStartRange(label='3-6', lookup_table={1: 3, 2: 4, 3: 5, 4: 6, 5: 6})
highest_fire_starts = FireStartRange(label='6+', lookup_table={1: 4, 2: 5, 3: 6, 4: 6, 5: 6})
all_ranges = [lowest_fire_starts, one_2_two_starts,
              two_2_three_starts, three_2_six_starts, highest_fire_starts]

kamloops_fire_starts = FireCentreFireStarts(
    fire_centre_id=1,
    lowest_fire_starts=lowest_fire_starts,
    one_2_two_starts=one_2_two_starts,
    two_2_three_starts=two_2_three_starts,
    three_2_six_starts=three_2_six_starts,
    highest_fire_starts=highest_fire_starts,
    all_ranges=all_ranges)


def get_fire_starts_by_fire_centre(fire_centre_id: int) -> FireCentreFireStarts:
    return kamloops_fire_starts
