# what?

```
sudo port select --set python python39
sudo port select --set python3 python39
```

```
sudo port selfupdate
sudo port upgrade outdated
sudo port install clang-14
pyenv install 3.8.12
```

## Using macports on m1

I had trouble using pyenv to install the version I need. So installing python with macports, and telling poetry to use the version I want.


```bash
sudo port selfupdate
sudo port upgrade outdated
sudo port install python38
```

this installs python 3.8 to: /opt/local/Library/Frameworks/Python.framework/Versions/3.8

```bash
poetry env use /opt/local/Library/Frameworks/Python.framework/Versions/3.8/bin
poetry install
```
