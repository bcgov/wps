I've tried to keep things related to the fire zone, fire centre and hfi polygons separate from the "app" module.

It makes sense to me, that it's NOT "app" code.

It does make the folder "api" redundant!


# step 1 - classify

```bash
python -m advisory.classify_hfi /my/path/to/hfi20220720.tif hfi_classified.tif
```

Validate output, manually:
qgis : TODO: elaborate

# step 2 - polygonize

```bash
python -m advisory.polygonize_hfi hfi_classified.tif hfi_classified.json <iso-formatted_date_of_file>
```

# step 3 - import into db

You can use ogr2ogr to import the json file into the database.

```bash
ogr2ogr -f "PostgreSQL" PG:"dbname=tileserv host=localhost user=tileserv password=tileserv" "hfi_classified.json" -nlt MULTIPOLYGON -lco precision=NO -nln hfi -overwrite
```



