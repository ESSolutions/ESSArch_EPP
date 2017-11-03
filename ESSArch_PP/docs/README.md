# ESSArch Preservation Platform Documentation

## Requirements
Install requirements using `pip install -r requirements_docs.txt` in the parent folder

## Generating documentation

Start by generating the source files

```
$ sphinx-apidoc -e -f -d 10 -o source ..
```

Then create the documentation files

```
$ make html
```

The output will be available in `_build/html`
