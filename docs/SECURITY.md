# Security policy

We take security issues seriously. We appreciate your efforts to responsibly disclose your findings, and will make every effort to acknowledge your contributions.

## Supported versions

This project doesn’t have formal support targets for non-latest versions. Backporting security fixes to affected releases will be decided on a case-by-case basis, based on effort involved and known usage of affected versions.

## Input handling

`ContentState` is normally deserialized from a rich text editor or a database, so it should be treated as untrusted input. The project uses [Property-based tests](CONTRIBUTING.md#property-based-tests) to check that rendering doesn’t crash on a wide range of generated `ContentState` inputs (empty text, zero-length ranges, unicode, deep nesting), across all supported engines. This reduces the risk of denial-of-service via malformed input. If you find an input that crashes the exporter or causes pathological resource usage, please report it as a vulnerability.

### Reporting a vulnerability

To report a vulnerability, please contact [@thibaudcolas](https://github.com/thibaudcolas) via email or with a DM [on Slack](SUPPORT.md#slack).
