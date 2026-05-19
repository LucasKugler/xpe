# Changelog

## Unreleased

### Changed
- Refactored `xpe` to expose core logic as importable functions (`evaluate_xpath`, `format_result`)
- Refactored `xte` to expose core logic as importable functions (`transform_xml`, `parse_xslt_params`)
- Refactored `xve` to expose core logic as importable functions (`load_schema`, `validate_xml`)
- Updated all tests to call core functions directly alongside subprocess tests for better coverage

## 1.2.0 - 2026-05-19

### Changed
- Removed manual encoding detection using chardet; lxml now handles encoding automatically
- Simplified file reading logic in `xte` and `xve` for massive performance improvement

### Added
- `-p/--param` flag for XSLT stylesheet parameters in `xte`

## 1.1.0 - 2026-05-19

### Added
- `xpe` - XPath parser tool for extracting data from XML/HTML
- `xte` - XSLT transformer tool for XML transformations
- `xve` - XML validation tool

### Changed
- Updated README with `xve` documentation
- Use XML parser by default

### Fixed
- Improved `xpe` output formatting
