# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Changed

- Placeholder for changes under development.

## 0.2.0

### Changed

- Narrowed the supported root API to the one-to-one `stable_marriage(...)`
  solver.
- Moved couples support behind the experimental
  `stable_marriage.experimental.stable_marriage_with_couples(...)` entry
  point.
- Raised the minimum supported Python version to 3.11.
- Expanded the packaging, CLI, validation, and documentation surface for the
  one-to-one solver and the experimental couples heuristic.

## 0.1.0

### Added

- Initial release of the `stable-marriage` package.
- Classical Gale-Shapley stable marriage solver exposed through the Python API.
- JSON-based command-line interface for solving one-to-one matching inputs.
- Initial couples-oriented matching experiments and supporting test fixtures.
