# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- **Scheduled Cache Prewarming**: Background scheduler that automatically fetches data from all configured sources
  - Configurable fetch intervals per data source (default: 25 minutes)
  - Automatic cache population before user requests
  - Significantly improved response times for all API calls
  - Support for enabling/disabling individual sources
  - Hot-reloadable configuration
  - Comprehensive metrics collection and status reporting
  - Graceful error handling and isolation
- New configuration file `scheduler_config.json` for scheduler settings
- Example configuration with all 30+ data sources pre-configured
- Detailed scheduler documentation in `docs/SCHEDULER.md`
- APScheduler dependency for task scheduling

### Changed
- Server now automatically starts scheduler on startup
- Cache is now pre-warmed, eliminating slow first-time requests
- Improved logging for scheduler operations

### Technical Details
- Scheduler runs in background threads, non-blocking
- Thread-safe metrics collection
- Automatic tool registry integration
- Configurable via environment variable `SCHEDULER_CONFIG_PATH`
- Default cache TTL: 30 minutes, default fetch interval: 25 minutes
