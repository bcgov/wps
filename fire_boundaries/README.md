# Fire Boundaries using Google Earth Engine

Google Earth Engine does not work on versions newer than 3.8.*

## Using macports on m1

I had trouble using pyenv to install the version I need. So installing python with macports, and telling poetry to use the version I want.


```bash
sudo port selfupdate
sudo port upgrade outdated
sudo port install python38
sudo port install gdal
```

this installs python 3.8 to: /opt/local/Library/Frameworks/Python.framework/Versions/3.8

```bash
poetry env use /opt/local/Library/Frameworks/Python.framework/Versions/3.8/bin
poetry run python -m pip install --upgrade pip
poetry install
poetry run python -m pip install gdal==$(gdal-config --version)
```
