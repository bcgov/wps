# Station weather data on object storage: layout diagram

The design is described in [station-predictions-storage.md](station-predictions-storage.md).

```mermaid
flowchart LR
    %% Nodes and edges are declared lane by lane, top to bottom. The order matters:
    %% it is what keeps the arrows from crossing, so keep it when editing.

    %% top lane: station history
    wf1src["WF1<br/>observations and forecasts"]
    wf1[("wf1<br/>every observation and forecast")]
    bytime[("by_time<br/>one value per station, time and source")]
    bystation["by_station<br/>history per station"]
    profile["hourly_profile<br/>statistics by month and hour of day"]
    r_profile(["Climatology screen<br/>a group, hourly"])
    r_station(["Climatology screen<br/>one station, or a group daily"])
    r_bytime(["MoreCast<br/>fire watch<br/>bias training, observations"])

    %% middle lane: model runs
    grib["Model GRIB files<br/>6 model jobs"]
    staging["staging<br/>partial run"]
    runs[("runs<br/>every model run, every lead")]
    r_runs(["/weather_models routes<br/>bias training"])

    %% bottom lane: every lead
    leads["leads<br/>every prediction at every lead"]
    r_leads(["Climatology at a chosen lead"])
    mc[("morecast_forecast<br/>Postgres")]

    wf1src --> wf1
    wf1 -- newest version wins --> bytime
    grib --> staging
    staging --> runs
    runs -- newest run wins --> bytime
    bytime --> bystation
    bystation --> profile
    profile --> r_profile
    bystation --> r_station
    bytime --> r_bytime
    runs --> r_runs
    runs --> leads
    mc --> leads
    leads --> r_leads

    classDef delta fill:#dbeafe,stroke:#1d4ed8,color:#111
    classDef parquet fill:#dcfce7,stroke:#15803d,color:#111
    classDef external fill:#f3f4f6,stroke:#6b7280,color:#111
    classDef reader fill:#fff,stroke:#6b7280,color:#111,stroke-dasharray: 3 3
    class runs,wf1,bytime delta
    class staging,leads,bystation,profile parquet
    class mc,grib,wf1src external
    class r_leads,r_runs,r_bytime,r_station,r_profile reader
```

Data flows from left to right, from raw to derived. Blue cylinders are Delta Lake tables, green boxes are plain Parquet files, grey nodes are outside this design, and dashed nodes are readers.

`runs` and `wf1` are the only permanent records; everything to their right can be deleted and rebuilt. The nightly job writes `by_station`, `hourly_profile` and `leads`. Run bookkeeping has no box because it has no storage of its own: a run's state is read from what exists in `staging` and `runs`.
