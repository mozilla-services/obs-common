# obs-common Graveyard

This document records interesting code that we've deleted for the sake of discoverability for the future.

## Various scripts

* [Removal PR](https://github.com/mozilla-services/obs-common/pull/161)

`obs_common/release.py` which determines a tag name based on the last tag and the current date. This was replaced with a `release.yml` GitHub Action workflow in each Crash Ingestion repo (e.g. [release.yml for Socorro](https://github.com/mozilla-services/socorro/blob/d79be5ed2bd532fc3fcd28b83f4a8860d2f823b5/.github/workflows/release.yml))
