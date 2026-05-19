# Changelog

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
