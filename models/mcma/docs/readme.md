# Documentation README

To compile the documentation `sphinx` package should be installed.

The structure of `doc/` directory is as follows:

- `source/`:
  - `conf.py` - contains configuration for the sphinx. Here we
    can define information about the project, change style (html theme)
    and so on.
  - `index.rst` - Main file of the documentation, here we define contents
    files that will be linked to it.
  - `readme.rst` - Contains installation instruction and basic usage.
    Should be update when the software will be done.
  - `user_guide.rst` - Contains descriptions of creating own model
    and detailed description of the configuration file.

To compile documentation in html one should run following command
from the `doc/` directory (it contains `Makefile` or `make.bat`
for windows):

```bash
make html
```

Sphinx will create `build/` directory. First page of the documentation
webpage is `build/html/index.html`.