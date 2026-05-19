# Changelog

## 1.2.1 - 2026-05-19

### Added
- Created `common.py` module with shared utilities (`read_input`, `read_content_or_file`)
- Added unit tests for `common.py` in `tests/test_common.py`

### Changed
- Refactored `xpe`, `xte`, `xve` to use shared utilities from `common.py`
- Removed `check_input_required` abstraction (inline checks are clearer)
- Refactored core logic as importable functions for better testability (`evaluate_xpath`, `format_result`, `transform_xml`, `parse_xslt_params`, `load_schema`, `validate_xml`)
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
