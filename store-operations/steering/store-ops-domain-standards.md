---
description: Store Operations domain standards — inventory, POS integration, and transaction rules for Kiro to follow in this product line.
---

# Store Operations — Domain Standards

## 1. Inventory Management

- **Never mutate stock levels outside a transaction.** All inventory updates must be wrapped in a database transaction. Use `@Transactional` (Java/Spring) or the equivalent for your stack.
- **Prevent negative inventory.** Before decrementing stock, check available quantity. If the result would be negative, throw a domain exception — never silently clamp to zero.
- **Reservation pattern.** When an order is placed, reserve stock immediately (status `RESERVED`). Only commit the deduction when the transaction is confirmed. Release the reservation on cancellation or timeout.

## 2. POS Integration

- **Idempotent event handlers.** Every handler that processes a POS event (sale, return, void, exchange) must guard against duplicate delivery. Use an idempotency key stored in a `processed_events` table or equivalent.
- **Backward-compatible contracts.** DTO fields consumed by POS systems must not be removed or have their type changed without a versioned migration plan. Add new fields as optional; deprecate old fields over at least one release cycle.
- **Event ordering.** POS events for a single transaction must be processed in order. Use a sequence number or event timestamp to detect and reject out-of-order messages.

## 3. Transactions and Consistency

- **Single responsibility per transaction.** Each database transaction should cover one business operation. Avoid spanning unrelated aggregates in a single transaction.
- **Saga pattern for distributed operations.** When an operation spans multiple services (e.g. inventory + loyalty + receipt), model it as a saga with compensating transactions rather than a distributed ACID transaction.
- **Optimistic locking.** Use optimistic locking (`@Version` or equivalent) on inventory and order records to prevent lost updates under concurrent access.

## 4. Audit Trail

- **Every state-changing operation must write an audit entry.** This includes: stock level changes, order status transitions, price overrides, and manual adjustments. Minimum audit fields: `entity_type`, `entity_id`, `action`, `performed_by`, `timestamp`, `before_value`, `after_value`.
- **Audit writes must be in the same transaction** as the state change. Never write audit records in a fire-and-forget async call.

## 5. Error Handling

- **Domain exceptions over generic exceptions.** Throw typed domain exceptions (`InsufficientStockException`, `DuplicateEventException`, etc.) rather than `RuntimeException` or `Exception`.
- **Never swallow exceptions silently.** If an error is caught and not re-thrown, it must be logged at `ERROR` level with full context (entity ID, operation, input values).

## 6. Testing Standards

- **Inventory and POS handler tests must cover the happy path, insufficient stock, and duplicate event scenarios** at minimum.
- **Use `@Transactional` on test methods** that write to the database to ensure rollback after each test.
- **Mock external POS calls** in unit tests; use WireMock or equivalent for integration tests.
