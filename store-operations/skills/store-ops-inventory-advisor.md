# Store Ops — Inventory Advisor Skill

## Purpose

This skill activates when you ask Kiro anything related to inventory logic in a store-operations repository. It makes Kiro behave as a domain expert in retail inventory management, applying store-operations standards automatically without you needing to repeat the rules each time.

## When This Skill Applies

Activate this skill when working on:
- Stock level calculations, reservations, or adjustments
- Inventory reconciliation jobs or reports
- POS transaction handlers that affect inventory
- Any service method with parameters or return types referencing `Inventory`, `StockLevel`, `Reservation`, or `InventoryAdjustment`

## Behaviour

When this skill is active, Kiro will:

1. **Always wrap inventory mutations in a transaction** — suggest `@Transactional` (or the stack equivalent) if it is missing.
2. **Enforce the reservation pattern** — when generating code that decrements stock, produce `RESERVE → CONFIRM / RELEASE` logic rather than a direct decrement.
3. **Add idempotency guards** on any method that processes an external event, using an idempotency-key check as the first statement in the handler.
4. **Include audit log writes** in the same transaction as every state change, using the standard audit fields: `entity_type`, `entity_id`, `action`, `performed_by`, `timestamp`, `before_value`, `after_value`.
5. **Suggest optimistic locking** (`@Version` or equivalent) when generating or reviewing entity classes that hold mutable stock or order state.
6. **Generate test cases** that cover at minimum: happy path, insufficient stock, and duplicate event scenarios.

## Example Prompts That Activate This Skill

- "Write a service method to process a POS sale event"
- "Generate an inventory adjustment endpoint"
- "Review this stock reconciliation job"
- "How should I model the stock reservation for a buy-online-pick-up-in-store flow?"

## References

- Domain standards: `store-ops-domain-standards.md` (injected into `.kiro/steering/`)
- Post-task review hook: `store-ops-spec-review-post-task.json` (injected into `.kiro/hooks/`)
