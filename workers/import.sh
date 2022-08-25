for file in `ls zones/*.json`; do
    echo $file
    ogr2ogr -f "PostgreSQL" PG:"dbname=tileserv host=localhost user=tileserv password=tileserv" $file -nlt MULTIPOLYGON -lco precision=NO -nln zones_wgs84
done