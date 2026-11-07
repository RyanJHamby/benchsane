# Changelog

All user-visible changes are recorded here. The project follows [Semantic Versioning](https://semver.org/) for the Python API in `benchsane.api` (not yet created), the CLI flags and exit codes, and the JSON schemas. Pre-1.0, minor releases may include breaking changes, and each is listed under "Changed".

## Unreleased

### Changed
- Renamed the project and package to `benchsane`; environment variables are now `BENCHSANE_KB_PATH` and `BENCHSANE_PAD`; the console scripts are `benchsane` and `benchsane-mcp`; schema ids are `benchsane.<name>/v1`.
- Minimum Python is now 3.10.
- The version now lives only in `src/benchsane/__init__.py`.

### Removed
- A personal tool reference in the bundled Skill.
