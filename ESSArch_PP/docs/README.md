# ESSArch Preservation Platform Documentation

## Requirements
Install requirements using `pip install -r /path/to/core/ESSArch_Core/requirements_docs.txt`

## Generating documentation for core

* Go to `docs` directory in core

```
cd /path/to/core/ESSArch_Core/docs
```

* Create `.pot`-files

```
make gettext
```

* Create/Update `.po`-files

```
sphinx-intl update -p _build/gettext -l {lang}
```

* Translate `.po`-files in `locale/{lang}/LC_MESSAGES/`

## Generating documentation for EPP

* Create a symlink named `core` pointing to the ESSArch Core docs

```
ln -s /path/to/core/ESSArch_Core/docs core
```

* Create `.pot`-files

```
make gettext
```

* Create/Update `.po`-files

```
sphinx-intl update -p _build/gettext -l {lang}
```

* Translate `.po`-files in `locale/{lang}/LC_MESSAGES/`

* Create symlink to core for each language

```
cd `locale/{lang}/LC_MESSAGES/`
rm -r core
ln -s /path/to/core/ESSArch_Core/docs/locale/{lang}/LC_MESSAGES core
```

* Create documents in each language

```
make html LANGUAGE="{lang}"
```
