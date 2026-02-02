# Test Cases (Web Asset Manager)

## Assets Screen
- TC-001: Assets screen loads and links to device/license lists.
- TC-002: Devices list loads before creation and shows the add button.
- TC-003: Licenses list loads before creation and shows the add button.
- TC-004: Create device with required fields succeeds and appears in the list.
- TC-005: Create license with required fields succeeds and appears in the list.
- TC-006: Search filter narrows the device list.
- TC-007: Sort columns change the device list order.
- TC-008: Edit device updates the list values.
- TC-009: Delete device removes the item from the list.
- TC-010: Sort columns change the license list order.
- TC-011: Edit license updates the list values.
- TC-012: Delete license removes the item from the list.

## Configurations Screen
- TC-011: Configurations screen loads and shows configuration cards.
- TC-012: Create configuration adds a new card and list row.
- TC-013: Edit configuration updates the list row.
- TC-014: Delete configuration removes the card and list row.
- TC-014-1: Configuration detail page shows assigned devices and licenses.
- TC-015: Drag device to a configuration assigns it.
- TC-016: Drag license to a configuration assigns it.
- TC-017: Drag configuration card updates stored position.

## System
- TC-018: Sample data is seeded on first startup.
- TC-019: Health endpoint returns ok.
