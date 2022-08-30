for file in `ls zones/*.json`; do
    echo $file
    ogr2ogr -f "PostgreSQL" PG:"dbname=wps host=localhost user=wps password=wps" $file -nlt MULTIPOLYGON -lco precision=NO -nln zones_wgs84
done