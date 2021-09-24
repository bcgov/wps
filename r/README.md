# R

The CFFDRS R package is used by wps.
renv is used to speed up github tests

## Updating the lockfile

Start R:

```bash
R
```

Install renv:

```R
install.packages('usethis')
install.packages("renv")
renv::install("cffdrs", dependencies = TRUE)
install.packages("cffdrs")
usethis::use_package("cffdrs")
renv::snapshot()
```
