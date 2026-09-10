# Configuration

`paths.example.toml` documents future local storage locations. Copy it to
`paths.local.toml` for machine-specific overrides only when a loader is added.
The scaffold does not load configuration or create data directories on import.

Future scientific specifications belong in versioned, non-sensitive TOML files
linked to a committed protocol. Do not add default pass speeds, reaction times,
orientation proxies, edge cutoffs, utility weights, or random split seeds before
their scientific decisions are justified. Local manifests with match membership
belong under ignored `data/manifests/`.
