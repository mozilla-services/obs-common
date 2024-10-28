# obs-common

code and commands shared between obs-team repositories

## service-status

Configure ``service-status`` in a couple of different ways:

1. A ``[tool.service-status]`` section in a ``pyproject.toml`` file in the
   current working directory.

2. Overridden by command-line arguments.

Keys:

``main_branch``

The name of the main branch in the git repository.

`hosts`

A list of hosts which have a ``/__version__`` Dockerflow endpoint in the
form of:

```
ENVIRONMENTNAME=HOST
```

For example:

```
prod=https://crash-stats.mozilla.org
```


Example `pyproject.toml`:

```toml
[tool.service-status]
main_branch = "main"
hosts = [
   "stage=https://crash-stats.allizom.org",
   "prod=https://crash-stats.mozilla.org",
]
```

For command help:

```shell
service-status --help
```

## license-check

Checks source files for license header.

For command help:

```shell
license-check --help
```

## sentry-wrap

Wraps a command such that if it fails, an error report is sent to the Sentry service specified by
`SENTRY_DSN` in the environment.

For command help:

```shell
sentry-wrap --help
```

## gcs-cli and pubsub-cli

Provides cli interfaces for interacting with various cloud service emulators used in our local dev
environments.

For command help:

```shell
gcs-cli --help
pubsub-cli --help
```

# History

`service-status` and `licence-check` were moved here from https://github.com/willkg/socorro-release,
while other scripts were moved here because they were being reused across various obs-team projects
such as https://github.com/mozilla-services/socorro and https://github.com/mozilla-services/antenna
