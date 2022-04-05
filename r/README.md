# R

The CFFDRS R package is used by wps.
renv is used to speed installing cffdrs for running github tests.

## macOSX

Instructions written for the following R version, please keep updated:

```
R version:
platform       x86_64-apple-darwin21.3.0
arch           x86_64
os             darwin21.3.0
system         x86_64, darwin21.3.0
status
major          4
minor          1.3
year           2022
month          03
day            10
svn rev        81868
language       R
version.string R version 4.1.3 (2022-03-10)
nickname       One Push-Up
```

For the R `usethis` dependency:
`brew install libgit2`

For the R `cffdrs` dependency:
`brew install libsodium`

## Linux

For the above (macOS) OS dependencies for linux

For the R `usethis` dependency:

```
deb: libgit2-dev (Debian, Ubuntu, etc)
rpm: libgit2-devel (Fedora, CentOS, RHEL)
```

For the R `cffdrs` dependency:

```
 deb: libsodium-dev (Debian, Ubuntu, etc)
 rpm: libsodium-devel (Fedora, EPEL)
 csw: libsodium_dev (Solaris)
```

## Installing from lockfile

```R
install.packages("renv")
renv::restore()
```

## Updating the lockfile

Updating the lockfile can be somewhat estoric for people (like myself) not familiar with R.

Start R:

```R
# usethis will be used to update the DESCRIPTION file
install.packages('usethis')
# renv will be used to create the lockfile
install.packages("renv")
renv::install('rgdal', depedencies = TRUE)
usethis::use_package('rgdal')
# instal cffdrs
renv::install("cffdrs", dependencies = TRUE)
# update the DESCRIPTION to list cffdrs as an import
usethis::use_package("cffdrs")
# install plumber
renv::install("plumber", dependencies = TRUE)
# update DESCRIPTION to list plumber as an import
usethis::use_package("plumber")
# create the lockfile
renv::snapshot()
```

## Running R API with Plumber

From `/r` directory:

Start R, and either restore/update the lockfile as necessary:

```R
renv::activate()
library(plumber)
pr = pr("cffdrs_api.r")
pr_run(pr)
```