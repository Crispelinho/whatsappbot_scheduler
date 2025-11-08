# Changelog

## [1.0.0] - 2025-08-18
### Added
- Celery integration for scheduled WhatsApp message sending.
- Celery Beat for periodic execution of message tasks.
- Admin import/export for appointments and messages (django-import-export).
- Automatic creation of scheduled messages and client messages when creating appointments (via signals).
- Centralized error handling using `ErrorCode` enum and `ErrorType` model.
- Retry logic for failed messages based on error type and retry count.
- Refactored sender logic to use a base interface for SOLID compliance.
- Service layer for message sending and error handling.
- Windows batch file for launching Celery worker and Beat easily.
- README documentation for manual, enqueued, and automated message sending workflows.
- Models for `ScheduledMessage`, `ClientScheduledMessage`, `MessageResponse`, `ErrorType`, and `Appointment`.

### Changed
- Improved code consistency and maintainability (SOLID principles).
- Updated admin and model relationships for robust bulk operations.

### Fixed
- Error handling and retry logic for network, timeout, and rate-limit errors.
- Consistent status and error code usage across the project.

---
