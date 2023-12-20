from dynaconf import Dynaconf

settings = Dynaconf(
    settings_files=["settings.json"],
)

# `envvar_prefix` = export envvars with `export DYNACONF_FOO=bar`.
# `settings_files` = Load these files in the order.