---
inclusion: always
---

# Node.js / TypeScript Coding Standards

These standards apply to all Node.js and TypeScript development on Southwest Airlines AI Engineering projects. Follow them consistently when writing new code and when modifying existing code.

---

## Project Structure

- Use a feature-based folder structure, not a type-based one. Prefer `src/crew/` over `src/controllers/`.
- Place all source files under `src/`. Compiled output goes to `dist/` (never committed).
- Tests live alongside source files or in a parallel `tests/` directory, mirroring `src/`.
- Configuration files at project root: `package.json`, `tsconfig.json`, `.eslintrc.json`, `.prettierrc`.

```
my-service/
├── src/
│   ├── crew/
│   │   ├── crew.controller.ts
│   │   ├── crew.service.ts
│   │   ├── crew.repository.ts
│   │   └── crew.types.ts
│   ├── common/
│   └── main.ts
├── tests/
│   └── crew/
├── tsconfig.json
├── package.json
└── .eslintrc.json
```

---

## Language: TypeScript First

- **All new code must be written in TypeScript.** Plain JavaScript is not accepted for new files.
- `strict: true` must be enabled in `tsconfig.json`. No exceptions.
- `noImplicitAny`, `strictNullChecks`, `strictFunctionTypes` must all be `true`.
- Do not use `any`. Use `unknown` when the type is genuinely unknown and narrow it explicitly.
- Do not use type assertions (`as SomeType`) to silence type errors — fix the type instead.
- Do not use `// @ts-ignore` or `// @ts-nocheck`. If you need to suppress a TS error, use `// @ts-expect-error` with a comment explaining why.

---

## Naming Conventions

| Element | Convention | Example |
|---|---|---|
| File | kebab-case | `crew-scheduler.service.ts` |
| Class | PascalCase | `CrewScheduler`, `FlightRepository` |
| Interface / Type | PascalCase | `CrewMember`, `AssignmentResult` |
| Function / Method | camelCase, verb-first | `assignCrew()`, `findByFlightId()` |
| Variable | camelCase | `crewMember`, `departureTime` |
| Constant (module-level) | UPPER_SNAKE_CASE | `MAX_FLIGHT_HOURS`, `DEFAULT_TIMEOUT_MS` |
| Enum | PascalCase members | `AssignmentStatus.Confirmed` |
| Test file | suffix with `.test.ts` or `.spec.ts` | `crew.service.test.ts` |

- Prefix interfaces with `I` only if there is a concrete class with the same name. Otherwise use plain names.
- Boolean variables and functions should read as predicates: `isAvailable`, `hasConflict`, `canBeAssigned`.

---

## Code Style

- Use **Prettier** for formatting. Config is committed to the repo — do not override per-file.
- 2-space indentation. No tabs.
- Single quotes for strings. Template literals for interpolation.
- Semicolons required.
- Maximum line length: 100 characters.
- Use **ESLint** with the Southwest shared config. All lint errors must be resolved before merging. Warnings must not increase.
- Run `npm run lint` and `npm run format:check` locally before opening a pull request.

---

## Imports and Modules

- Use ES module syntax (`import`/`export`). Never `require()` in TypeScript files.
- Use absolute imports configured via `tsconfig.json` `paths` — avoid long relative chains (`../../../`).
- Organize imports: Node built-ins → third-party → local aliases → relative. Separated by blank lines.
- Only import what you use. No `import * as` unless working with a module that doesn't support named exports.
- Re-export intentionally from `index.ts` barrel files. Do not barrel-export everything blindly.

```typescript
// Good
import { readFile } from 'fs/promises';

import { Injectable } from '@nestjs/common';

import { CrewRepository } from '@crew/crew.repository';
import { AssignmentResult } from './crew.types';
```

---

## Functions and Methods

- Functions should do one thing. If a function needs comments to explain each block, split it.
- Maximum function length: 30 lines. Refactor anything longer.
- Maximum parameter count: 3. Use an options object for more.
- Return early to reduce nesting. Avoid deeply nested `if` blocks.
- Prefer `async`/`await` over `.then()`/`.catch()` chains for readability.
- Always `await` Promises. Never fire-and-forget unless the intent is explicit and documented.
- Mark functions `async` only if they contain `await` or return a `Promise` explicitly.

```typescript
// Good
async function assignCrew(flightId: number, memberId: number): Promise<Assignment> {
  const member = await crewRepository.findById(memberId);
  if (!member.isAvailable) {
    throw new CrewUnavailableError(`Member ${memberId} is not available`);
  }
  return assignmentRepository.create({ flightId, memberId });
}
```

---

## Classes and Interfaces

- Use `interface` for object shapes and public API contracts. Use `type` for unions, intersections, and aliases.
- Keep classes focused on a single responsibility.
- Use constructor injection for dependencies. Do not instantiate dependencies inside a class.
- Mark fields `private` or `readonly` by default. Expose state through deliberate accessors.
- Prefer `readonly` arrays and objects where mutation is not intended: `readonly string[]`.
- Avoid `enum` for string-valued sets — use `const` objects with `as const` for better tree-shaking and type safety.

```typescript
// Prefer this
const AssignmentStatus = {
  Pending: 'PENDING',
  Confirmed: 'CONFIRMED',
  Cancelled: 'CANCELLED',
} as const;
type AssignmentStatus = typeof AssignmentStatus[keyof typeof AssignmentStatus];

// Over this
enum AssignmentStatus { Pending, Confirmed, Cancelled }
```

---

## Error Handling

- Use typed error classes. Never `throw new Error('something failed')` at a domain boundary.
- Never swallow errors silently. At minimum, log before rethrowing.
- Handle `Promise` rejections. Every `async` function must either `try/catch` or propagate the error to a handler.
- In Express/NestJS, use centralized error middleware / exception filters — do not handle HTTP error responses in individual controllers.
- Distinguish operational errors (bad input, unavailable resource) from programming errors (null dereference, assertion failure).

```typescript
// Good
export class CrewUnavailableError extends Error {
  constructor(message: string, public readonly memberId: number) {
    super(message);
    this.name = 'CrewUnavailableError';
  }
}
```

---

## Logging

- Use a structured logger — **Pino** is the standard. Never use `console.log` in production code.
- Log as JSON in production. Human-readable format is acceptable in local dev only.
- Log levels: `fatal`, `error`, `warn`, `info`, `debug`, `trace`. Use them consistently.
- Include structured context fields — do not interpolate values into the message string.
- Never log passwords, tokens, PII, or card numbers at any level.
- Redact sensitive fields in the Pino config (`redact` option) as a safety net.

```typescript
// Good
log.info({ flightId, memberId }, 'Assigning crew member to flight');

// Bad
console.log(`Assigning crew member ${memberId} to flight ${flightId}`);
log.info(`Assigning crew member ${memberId} to flight ${flightId}`);
```

---

## Async Patterns

- Use `Promise.all()` for concurrent independent async operations. Never `await` in a loop when operations are independent.
- Use `Promise.allSettled()` when you need all results regardless of individual failures.
- Avoid mixing callbacks and Promises. Promisify callback-based APIs with `util.promisify` or the `promises` variant of Node built-ins.
- Set explicit timeouts on all external calls (HTTP, DB, cache). Never make unbounded network calls.

```typescript
// Good — parallel
const [crew, flight] = await Promise.all([
  crewRepository.findById(memberId),
  flightRepository.findById(flightId),
]);

// Bad — sequential when independent
const crew = await crewRepository.findById(memberId);
const flight = await flightRepository.findById(flightId);
```

---

## Security

- Never hardcode credentials, API keys, or secrets. Use environment variables loaded via a validated config module (e.g., `zod` schema over `process.env`).
- Validate all external input using a schema library (**Zod** is the standard). Never trust `req.body` directly.
- Use parameterized queries with your ORM or query builder. Never concatenate user input into SQL or NoSQL queries.
- Set `helmet` middleware on all Express/NestJS apps.
- Set explicit `Content-Security-Policy`, `X-Content-Type-Options`, and `Strict-Transport-Security` headers.
- Audit dependencies with `npm audit` before adding new packages. Run `npm audit` in CI.

---

## Dependency Management

- Pin all dependencies to exact versions in `package.json` for applications. Use `^` (caret) only in library `package.json`.
- Commit `package-lock.json`. Never delete or gitignore it.
- Separate runtime (`dependencies`) from dev-only (`devDependencies`) packages correctly.
- Review `npm audit` output before merging. No high or critical vulnerabilities on new code.
- Prefer packages with active maintenance, wide adoption, and TypeScript types included or in `@types/`.

---

## REST API Design

- Use nouns for resource paths, not verbs: `/crew-members`, not `/getCrewMembers`.
- Use standard HTTP methods: `GET` (read), `POST` (create), `PUT` (full replace), `PATCH` (partial update), `DELETE`.
- Return appropriate HTTP status codes: `200`, `201`, `204`, `400`, `401`, `403`, `404`, `409`, `500`.
- Version APIs via the path: `/api/v1/crew-members`.
- Return consistent error response bodies with `timestamp`, `statusCode`, `error`, and `message` fields.
- Use `application/json` for all request and response bodies.

---

## Testing Standards

- Use **Jest** as the test runner. Use `ts-jest` for TypeScript support.
- Every public service method must have at least one test for the happy path and one for failure/edge cases.
- Use `jest.mock()` or manual mocks for external dependencies. Do not make real network or DB calls in unit tests.
- Test names describe the scenario: `assignCrew > throws CrewUnavailableError when member is not available`.
- Aim for 80%+ line coverage on `src/` packages. Test behavior, not implementation details.
- Use `describe` to group related tests and `beforeEach` for shared setup.
- Keep tests independent and idempotent. No shared mutable state between test cases.

```typescript
describe('CrewScheduler', () => {
  describe('assignCrew', () => {
    it('throws CrewUnavailableError when member is not available', async () => {
      const mockRepo = { findById: jest.fn().mockResolvedValue({ isAvailable: false }) } as any;
      const scheduler = new CrewScheduler(mockRepo);

      await expect(scheduler.assignCrew(42, 7)).rejects.toThrow(CrewUnavailableError);
    });
  });
});
```

---

## Documentation

- Every exported function, class, and interface must have a JSDoc comment.
- JSDoc should explain **what** and **why** — not a restatement of the code.
- Use `@param`, `@returns`, and `@throws` tags for public API functions.
- Keep documentation current. A stale comment is worse than none.

---

## CI Checklist

Before opening a pull request, all of the following must pass locally:

| Tool | Purpose | Command |
|---|---|---|
| `prettier` | Formatting | `npm run format:check` |
| `eslint` | Linting | `npm run lint` |
| `tsc` | Type checking | `npx tsc --noEmit` |
| `jest` | Tests + coverage | `npm test -- --coverage` |
| `npm audit` | Dependency security | `npm audit --audit-level=high` |
