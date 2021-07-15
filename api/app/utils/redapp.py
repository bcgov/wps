""" Call Java REDapp code.

If jnius wasn't prone throwing segmentation faults, we wouldn't need this level of indirection.
"""
from datetime import datetime, date
import jnius_config
# import jnius - importing jnius on this level causes an segmentation fault.
from app import config

jnius_config.set_classpath(config.get('CLASSPATH'))


class FWICalculations:  # pylint: disable=missing-class-docstring, too-many-instance-attributes
    """ Duplicate of Java class ca.cwfgm.fwi.FWICalculations for results """

    def __init__(self):   # pylint: disable=too-many-statements
        """ Init variables """
        # pylint: disable=invalid-name
        self.ystrdyFFMC: float = None
        self.ystrdyDMC: float = None
        self.ystrdyDC: float = None
        self.noonTemp: float = None
        self.noonRH: float = None
        self.noonPrecip: float = None
        self.noonWindSpeed: float = None
        self.hrlyTemp: float = None
        self.hrlyRH: float = None
        self.hrlyPrecip: float = None
        self.hrlyWindSpeed: float = None
        self.dlyFFMC: float = None
        self.dlyDMC: float = None
        self.dlyDC: float = None
        self.dlyISI: float = None
        self.dlyBUI: float = None
        self.dlyFWI: float = None
        self.dlyDSR: float = None
        self.hlyHFFMC: float = None
        self.hlyHISI: float = None
        self.hlyHFWI: float = None
        self.prvhlyFFMC: float = None
        self.calcHourly: bool = None
        self.useVanWagner: bool = None
        self.useLawsonPreviousHour: bool = False
        self.m_date: datetime = None
        self.m_init_timezone_code: str = None


def FWICalculateDailyStatisticsCOM(longitude: float,  # pylint: disable=invalid-name, too-many-arguments
                                   latitude: float,
                                   yesterday_ffmc: float,
                                   yesterday_dmc: float,
                                   yesterday_dc: float,
                                   noon_temp: float,
                                   noon_rh: float,
                                   noon_precip: float,
                                   noon_wind_speed: float,
                                   calc_hourly: bool,
                                   hourly_temp: float,
                                   hourly_rh: float,
                                   hourly_precip: float,
                                   hourly_wind_speed: float,
                                   previous_hourly_ffmc: float,
                                   use_van_wagner: bool,
                                   use_lawson_previous_hour: bool,
                                   time_of_interest: datetime) -> FWICalculations:
    """ Take input parameters to calculate FWI and pass to REDapp java instance of class
    ca.cwfgm.fwi.FWICalculations. Then call FWICalculateDailyStatisticsCOM on instance, and
    copy results into response object.
    """
    # pylint: disable=too-many-locals
    # we have to do a late import, otherwise we get a segmentation fault.
    import jnius  # pylint: disable=import-outside-toplevel
    try:
        Calendar = jnius.autoclass('java.util.Calendar')  # pylint: disable=invalid-name
        TimeZone = jnius.autoclass('java.util.TimeZone')  # pylint: disable=invalid-name
        FWICalculationsClass = jnius.autoclass('ca.cwfgm.fwi.FWICalculations')  # pylint: disable=invalid-name

        fwi = FWICalculationsClass()
        fwi.setLatitude(latitude)
        fwi.setLongitude(longitude)
        fwi.ystrdyFFMC = yesterday_ffmc
        fwi.ystrdyDMC = yesterday_dmc
        fwi.ystrdyDC = yesterday_dc
        fwi.noonTemp = noon_temp
        fwi.noonRH = noon_rh
        fwi.noonPrecip = noon_precip
        fwi.noonWindSpeed = noon_wind_speed
        fwi.calcHourly = calc_hourly
        fwi.hrlyTemp = hourly_temp
        fwi.hrlyRH = hourly_rh
        fwi.hrlyPrecip = hourly_precip
        fwi.hrlyWindSpeed = hourly_wind_speed
        fwi.prvhlyFFMC = previous_hourly_ffmc
        fwi.useVanWagner = use_van_wagner
        fwi.useLawsonPreviousHour = use_lawson_previous_hour

        m_date = Calendar.getInstance(TimeZone.getTimeZone(time_of_interest.tzinfo.tzname(time_of_interest)))
        m_date.set(time_of_interest.year, time_of_interest.month, time_of_interest.day,
                   time_of_interest.hour, time_of_interest.minute, time_of_interest.second)
        fwi.m_date = m_date

        fwi.FWICalculateDailyStatisticsCOM()

        copy = FWICalculations()
        for key in dir(copy):
            if '__' not in key:
                if key == 'm_date':
                    # TODO: Sybrand - figure out the timezone stuff
                    copy.m_date = datetime(fwi.m_date.get(Calendar.YEAR),
                                           fwi.m_date.get(Calendar.MONTH),
                                           fwi.m_date.get(Calendar.DAY_OF_MONTH),
                                           fwi.m_date.get(Calendar.HOUR),
                                           fwi.m_date.get(Calendar.MINUTE),
                                           fwi.m_date.get(Calendar.SECOND))
                else:
                    setattr(copy, key, getattr(fwi, key))

        return copy

    finally:
        # Each time you create a native thread in Python and use Pyjnius, any call to Pyjnius
        # methods will force attachment of the native thread to the current JVM. But you must
        # detach it before leaving the thread, and Pyjnius cannot do it for you.
        jnius.detach()  # pylint: disable=no-member


class FBPCalculations:  # pylint: disable=missing-class-docstring, too-many-instance-attributes
    """ Duplicate of Java class ca.cwfgm.fbp.FBPCalculations

    public double ros_t;
    public double ros_eq;
    public double fros;
    public double bros;
    public double rso;
    public double hfi;
    public double ffi;
    public double bfi;
    public double area;
    public double perimeter;
    public double distanceHead;
    public double distanceFlank;
    public double distanceBack;
    public double lb;
    public double csi;
    public double cfb;
    public double sfc;
    public double tfc;
    public double cfc;
    public double isi;
    public double fmc;
    public double wsv;
    public double raz;
    public double conifMixedWood;
    public double deadBalsam;
    public double grassCuring;
    public double grassFuelLoad;
    public double crownBase;
    public double elapsedTime;
    public double ffmc;
    public double windSpeed;
    public double windDirection;
    public double bui;
    public double dmc;
    public double dc;
    public double slopeValue;
    public double aspect;
    public double latitude;
    public double longitude;
    public double elevation;
    public boolean acceleration;
    public boolean useCrownBaseHeight;
    public boolean useBui;
    public boolean useBuildup;
    public boolean useSlope;
    public boolean useGreenup;
    public int fuelType;
    public String fireDescription;
    public String headFireDescription;
    public String flankFireDescription;
    public String backFireDescription;

    public Calendar m_date;

    public boolean cfbPossible = true;
    """

    def __init__(self):  # pylint: disable=too-many-statements
        """ Init variables """
        # pylint: disable=invalid-name
        self.ros_t: float = None
        self.ros_eq: float = None
        self.fros: float = None
        self.bros: float = None
        self.rso: float = None
        self.hfi: float = None
        self.ffi: float = None
        self.bfi: float = None
        self.area: float = None
        self.perimeter: float = None
        self.distanceHead: float = None
        self.distanceFlank: float = None
        self.distanceBack: float = None
        self.lb: float = None
        self.csi: float = None
        self.cfb: float = None
        self.sfc: float = None
        self.tfc: float = None
        self.cfc: float = None
        self.isi: float = None
        self.fmc: float = None
        self.wsv: float = None
        self.raz: float = None
        self.conifMixedWood: float = None
        self.deadBalsam: float = None
        self.grassCuring: float = None
        self.grassFuelLoad: float = None
        self.crownBase: float = None
        self.elapsedTime: float = None
        self.ffmc: float = None
        self.windSpeed: float = None
        self.windDirection: float = None
        self.bui: float = None
        self.dmc: float = None
        self.dc: float = None
        self.slopeValue: float = None
        self.aspect: float = None
        self.latitude: float = None
        self.longitude: float = None
        self.elevation: float = None
        self.acceleration: bool = None
        self.useCrownBaseHeight: bool = None
        self.useBui: bool = None
        self.useBuildup: bool = None
        self.useSlope: bool = None
        self.useGreenup: bool = None
        self.fuelType: int = None
        self.fireDescription: str = None
        self.headFireDescription: str = None
        self.flankFireDescription: str = None
        self.backFireDescription: str = None
        self.m_date: date = None
        self.cfbPossible: bool = True


class UnmappedFuelType(Exception):
    """ Raised for fuel types that don't have an index mapping """


def _fbp_fuel_type_map(fuel_type: str):
    """
    This is messy. REDapp has a combo box with fuel types, which it then maps
    to a fuel type index.

    new FuelValue(Cwfgm_Fuel_C1.class, "C-1:  Spruce-Lichen Woodland"),
    new FuelValue(Cwfgm_Fuel_C2.class, "C-2:  Boreal Spruce"),
    new FuelValue(Cwfgm_Fuel_C3.class, "C-3:  Mature Jack or Lodgepole Pine"),
    new FuelValue(Cwfgm_Fuel_C4.class, "C-4:  Immature Jack or Lodgepole Pine"),
    new FuelValue(Cwfgm_Fuel_C5.class, "C-5:  Red and White Pine"),
    new FuelValue(Cwfgm_Fuel_C6.class, "C-6:  Conifer Plantation"),
    new FuelValue(Cwfgm_Fuel_C7.class, "C-7:  Ponderosa Pine / Douglas Fir"),
    new FuelValue(Cwfgm_Fuel_D1.class, "D-1:  Leafless Aspen"),
    new FuelValue(Cwfgm_Fuel_D2.class, "D-2:  Green Aspen (w/ BUI Thresholding)"),
    new FuelValue(Cwfgm_Fuel_D1D2.class, "D-1/D-2:  Aspen"),
    new FuelValue(Cwfgm_Fuel_M1.class, "M-1:  Boreal Mixedwood - Leafless"),
    new FuelValue(Cwfgm_Fuel_M2.class, "M-2:  Boreal Mixedwood - Green"),
    new FuelValue(Cwfgm_Fuel_M1M2.class, "M-1/M-2:  Boreal Mixedwood"),
    new FuelValue(Cwfgm_Fuel_M3.class, "M-3:  Dead Balsam Fir / Mixedwood - Leafless"),
    new FuelValue(Cwfgm_Fuel_M4.class, "M-4:  Dead Balsam Fir / Mixedwood - Green"),
    new FuelValue(Cwfgm_Fuel_M3M4.class, "M-3/M-4:  Dead Balsam Fir / Mixedwood"),
    new FuelValue(Cwfgm_Fuel_O1a.class, "O-1a:  Matted Grass"),
    new FuelValue(Cwfgm_Fuel_O1b.class, "O-1b:  Standing Grass"),
    new FuelValue(Cwfgm_Fuel_O1ab.class, "O-1ab:  Grass"),
    new FuelValue(Cwfgm_Fuel_S1.class, "S-1:  Jack or Lodgepole Pine Slash"),
    new FuelValue(Cwfgm_Fuel_S2.class, "S-2:  White Spruce / Balsam Slash"),
    new FuelValue(Cwfgm_Fuel_S3.class, "S-3:  Coastal Cedar / Hemlock / Douglas-Fir Slash") };

    comboIndexToFuel.put(Integer.valueOf(0), Integer.valueOf(0));
    comboIndexToFuel.put(Integer.valueOf(1), Integer.valueOf(1));
    comboIndexToFuel.put(Integer.valueOf(2), Integer.valueOf(2));
    comboIndexToFuel.put(Integer.valueOf(3), Integer.valueOf(3));
    comboIndexToFuel.put(Integer.valueOf(4), Integer.valueOf(4));
    comboIndexToFuel.put(Integer.valueOf(5), Integer.valueOf(5));
    comboIndexToFuel.put(Integer.valueOf(6), Integer.valueOf(6));
    comboIndexToFuel.put(Integer.valueOf(7), Integer.valueOf(7));
    comboIndexToFuel.put(Integer.valueOf(8), Integer.valueOf(8));
    comboIndexToFuel.put(Integer.valueOf(9), Integer.valueOf(10));
    comboIndexToFuel.put(Integer.valueOf(10), Integer.valueOf(11));
    comboIndexToFuel.put(Integer.valueOf(11), Integer.valueOf(13));
    comboIndexToFuel.put(Integer.valueOf(12), Integer.valueOf(14));
    comboIndexToFuel.put(Integer.valueOf(13), Integer.valueOf(16));
    comboIndexToFuel.put(Integer.valueOf(14), Integer.valueOf(17));
    comboIndexToFuel.put(Integer.valueOf(15), Integer.valueOf(18));
    comboIndexToFuel.put(Integer.valueOf(16), Integer.valueOf(19));
    comboIndexToFuel.put(Integer.valueOf(17), Integer.valueOf(20));
    comboIndexToFuel.put(Integer.valueOf(18), Integer.valueOf(21));

    combobox index -> fuel type index
    0:0 "C-1:  Spruce-Lichen Woodland"
    1:1 "C-2:  Boreal Spruce"
    2:2 "C-3:  Mature Jack or Lodgepole Pine"
    3:3 "C-4:  Immature Jack or Lodgepole Pine"
    4:4 "C-5:  Red and White Pine"
    5:5 "C-6:  Conifer Plantation"
    6:6 "C-7:  Ponderosa Pine / Douglas Fir"
    7:7 "D-1:  Leafless Aspen"
    8:8 "D-2:  Green Aspen (w/ BUI Thresholding)"
    9:10 "D-1/D-2:  Aspen"
    10:11 "M-1:  Boreal Mixedwood - Leafless"
    11:13 "M-2:  Boreal Mixedwood - Green"
    12:14 "M-1/M-2:  Boreal Mixedwood"
    13:16 "M-3:  Dead Balsam Fir / Mixedwood - Leafless"
    14:17 "M-4:  Dead Balsam Fir / Mixedwood - Green"
    15:18 "M-3/M-4:  Dead Balsam Fir / Mixedwood"
    16:19 "O-1a:  Matted Grass"
    17:20 "O-1b:  Standing Grass"
    18:21 "O-1ab:  Grass"
    19"S-1:  Jack or Lodgepole Pine Slash"
    20"S-2:  White Spruce / Balsam Slash"
    21"S-3:  Coastal Cedar / Hemlock / Douglas-Fir Slash"
    """
    # fuel_type_map = {
    #     'C1': 0,
    #     'C2': 1,
    #     'C3': 2,
    #     'C4': 3,
    #     'C5': 4,
    #     'C6': 5,
    #     'C7': 6,
    #     'D1': 7,
    #     'D2': 8,
    #     # D1/D2: Aspen # we don't have this as a dropdown right now!
    #     'M1': 11,
    #     'M2': 13,
    #     # M1/M2: Boreal Mixedwood # we don't have this as a dropdown right now!
    #     'M3': 16,
    #     'M4': 17,
    #     # M3/M4: Dead Balsam Fir / Mixedwood # we don't have this as a dropdown right now!
    #     'O1A': 19,
    #     'O1B': 20,
    #     # O1ab: Grass # we don't have this as a dropdown right now!
    #     # 'S1': - no mapping
    #     # 'S2': - no mapping
    #     # 'S3': - no mapping
    # }
    fuel_type_map = {
        'C1': 0,
        'C2': 1,
        'C3': 2,
        'C4': 3,
        'C5': 4,
        'C6': 5,
        'C7': 6,
        'D1': 7,
        'D2': 8,
        # D1/D2: Aspen # we don't have this as a dropdown right now!
        'M1': 10,
        'M2': 11,
        # M1/M2: Boreal Mixedwood # we don't have this as a dropdown right now!
        'M3': 13,
        'M4': 14,
        # M3/M4: Dead Balsam Fir / Mixedwood # we don't have this as a dropdown right now!
        'O1A': 16,
        'O1B': 17,
        # O1ab: Grass # we don't have this as a dropdown right now!
        'S1': 19,
        'S2': 20,
        'S3': 21
    }
    if fuel_type in fuel_type_map:
        return fuel_type_map[fuel_type]
    raise UnmappedFuelType(fuel_type)


def FBPCalculateStatisticsCOM(elevation: float,  # pylint: disable=invalid-name, too-many-arguments
                              latitude: float,
                              longitude: float,
                              time_of_interest: datetime,
                              fuel_type: str,
                              ffmc: float,
                              dmc: float,
                              dc: float,
                              bui: float,
                              wind_speed: float,
                              wind_direction: float,
                              percentage_conifer: float,
                              percentage_dead_balsam_fir: float,
                              grass_cure: float,
                              crown_base_height: float) -> FBPCalculations:
    """ Uses method FBPCalculateStatisticsCOM on class ca.cwfgm.fbp.FBPCalculations to calculate
    fire behaviour.

    public class FBPCalculations {

        # methods:
        public FBPCalculations() {
        initializeInputValues();
        initializeOutputValues();
        }
        public void FBPCalculateStatisticsCOM()
    }
    """
    # pylint: disable=too-many-locals
    # we have to do a late import, otherwise we get a segmentation fault.
    import jnius  # pylint: disable=import-outside-toplevel
    try:
        Calendar = jnius.autoclass('java.util.Calendar')  # pylint: disable=invalid-name
        TimeZone = jnius.autoclass('java.util.TimeZone')  # pylint: disable=invalid-name
        FBPCalculationsClass = jnius.autoclass('ca.cwfgm.fbp.FBPCalculations')  # pylint: disable=invalid-name

        if percentage_dead_balsam_fir is None:
            percentage_dead_balsam_fir = 0.0
        if grass_cure is None:
            grass_cure = 0.0
        if crown_base_height is None:
            use_crown_base_height = False
            crown_base_height = 0.0
        else:
            use_crown_base_height = True
        if percentage_conifer is None:
            percentage_conifer = 0.0

        fbp = FBPCalculationsClass()
        fbp.elevation = elevation
        fbp.latitude = latitude
        fbp.longitude = longitude
        fbp.ffmc = ffmc
        fbp.dmc = dmc
        fbp.dc = dc
        fbp.useBui = True
        fbp.useBuildup = True
        fbp.bui = bui
        fbp.windSpeed = wind_speed
        fbp.windDirection = wind_direction
        fbp.fuelType = _fbp_fuel_type_map(fuel_type)
        fbp.conifMixedWood = percentage_conifer
        fbp.deadBalsam = percentage_dead_balsam_fir
        fbp.grassCuring = grass_cure
        fbp.crownBase = crown_base_height

        fbp.useSlope = False
        fbp.useCrownBaseHeight = use_crown_base_height

        # TODO: Sybrand figure out timezone
        gmt = Calendar.getInstance(TimeZone.getTimeZone("GMT"))
        gmt.set(time_of_interest.year, time_of_interest.month, time_of_interest.day,
                time_of_interest.hour, time_of_interest.minute, time_of_interest.second)
        fbp.m_date = gmt
        fbp.FBPCalculateStatisticsCOM()

        # we copy the java object into a python object, so that we can safel detach from the java VM
        # when we exit this function.
        copy = FBPCalculations()
        for key in dir(copy):
            if '__' not in key:
                if key == 'm_date':
                    copy.m_date = date(fbp.m_date.get(Calendar.YEAR),
                                       fbp.m_date.get(Calendar.MONTH),
                                       fbp.m_date.get(Calendar.DAY_OF_MONTH))
                else:
                    setattr(copy, key, getattr(fbp, key))

        return copy
    finally:
        # Each time you create a native thread in Python and use Pyjnius, any call to Pyjnius
        # methods will force attachment of the native thread to the current JVM. But you must
        # detach it before leaving the thread, and Pyjnius cannot do it for you.
        jnius.detach()  # pylint: disable=no-member


def hourlyFFMCLawson(prevFFMC: float,  # pylint: disable=invalid-name
                     currFFMC: float,
                     rh: float,
                     seconds_into_day: int) -> float:
    """ Ok - great - but what does this even do? """
    import jnius  # pylint: disable=import-outside-toplevel
    try:
        CwfgmFwi = jnius.autoclass('ca.cwfgm.fwi.CwfgmFwi')  # pylint: disable=invalid-name
        return CwfgmFwi.hourlyFFMCLawson(prevFFMC, currFFMC, rh, seconds_into_day)
    finally:
        jnius.detach()  # pylint: disable=no-member
