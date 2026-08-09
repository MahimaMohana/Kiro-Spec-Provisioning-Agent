---
inclusion: always
---

# Java Coding Standards

These standards apply to all Java development on Southwest Airlines AI Engineering projects. Follow them consistently when writing new code and when modifying existing code.

---

## Project Structure

- Follow standard Maven/Gradle layout: `src/main/java`, `src/test/java`, `src/main/resources`.
- Package names use reverse domain notation in lowercase: `com.southwest.<team>.<service>`.
- Group classes by feature/domain layer, not by type. Prefer `com.southwest.crew.scheduling` over `com.southwest.controller`.
- One top-level public class per file. The filename must match the class name exactly.

---

## Naming Conventions

| Element | Convention | Example |
|---|---|---|
| Class / Interface | PascalCase | `CrewScheduler`, `FlightRepository` |
| Method | camelCase, verb-first | `assignCrew()`, `findByFlightId()` |
| Variable | camelCase | `crewMember`, `departureTime` |
| Constant | UPPER_SNAKE_CASE | `MAX_FLIGHT_HOURS`, `DEFAULT_TIMEOUT_MS` |
| Package | lowercase, no underscores | `com.southwest.crew.service` |
| Test class | Suffix with `Test` | `CrewSchedulerTest` |

- Avoid abbreviations unless they are industry-standard (e.g., `dto`, `id`, `url`).
- Boolean methods should read as predicates: `isAvailable()`, `hasConflict()`, `canBeAssigned()`.

---

## Code Style

- Use 4-space indentation. No tabs.
- Maximum line length: 120 characters.
- Opening braces on the same line as the declaration (K&R style).
- Always use braces for `if`, `for`, `while` blocks, even single-line ones.
- Add a blank line between methods and between logical sections within a method.
- Remove unused imports. Organize imports: static imports last, alphabetical within groups.

---

## Class Design

- Keep classes focused on a single responsibility (SRP).
- Prefer composition over inheritance.
- Mark fields `private` by default. Expose state only through deliberate accessors.
- Use `final` for fields that are set once (constructor injection).
- Utility classes with only static methods must have a private no-arg constructor and be declared `final`.
- Avoid mutable static state.

---

## Methods

- Methods should do one thing. If a method needs a comment to explain what each block does, split it.
- Maximum method length: 30 lines. Refactor anything longer.
- Maximum parameter count: 4. Use a request/context object for more.
- Return early to reduce nesting. Avoid deeply nested `if` blocks.
- Never return `null` from a public method — use `Optional<T>` or throw a meaningful exception.
- Avoid `boolean` parameters that toggle behavior; use two separate methods or an enum instead.

---

## Exception Handling

- Use specific exception types. Never `catch (Exception e)` or `catch (Throwable t)` unless at a top-level boundary.
- Never swallow exceptions silently. At minimum, log before rethrowing.
- Checked exceptions are for recoverable conditions. Use unchecked (runtime) exceptions for programming errors.
- Create domain-specific exception classes when a caller needs to handle a failure distinctly.
- Always include a meaningful message in thrown exceptions. Include relevant context (IDs, values).
- Clean up resources with try-with-resources. Never rely on `finally` for stream/connection closing.

```java
// Good
try (var stream = Files.newInputStream(path)) {
    return parseManifest(stream);
} catch (IOException e) {
    throw new ManifestLoadException("Failed to load manifest from: " + path, e);
}

// Bad
try {
    InputStream stream = new FileInputStream(file);
    return parseManifest(stream);
} catch (Exception e) {
    e.printStackTrace();
}
```

---

## Logging

- Use SLF4J with Logback. Never use `System.out.println` or `java.util.logging` directly.
- Inject the logger as a `private static final` field using `LoggerFactory.getLogger(ClassName.class)`.
- Use parameterized logging — never string concatenation in log statements.
- Log levels:
  - `ERROR`: System failures requiring immediate attention.
  - `WARN`: Unexpected conditions that are recoverable.
  - `INFO`: Key business events (service start, significant state changes).
  - `DEBUG`: Diagnostic details useful during development.
  - `TRACE`: Fine-grained execution flow (disabled in production).
- Never log passwords, tokens, PII, or card numbers at any level.

```java
// Good
log.debug("Assigning crew member {} to flight {}", memberId, flightId);

// Bad
log.debug("Assigning crew member " + memberId + " to flight " + flightId);
```

---

## Null Safety

- Validate method arguments at the entry point using `Objects.requireNonNull()` or Spring's `Assert`.
- Use `Optional<T>` for return types when absence is a valid and expected outcome.
- Never pass `null` as a method argument intentionally — use `Optional` or overloaded methods.
- Annotate with `@NonNull` / `@Nullable` (from `org.springframework.lang`) to document intent.

---

## Collections and Streams

- Prefer immutable collections for return types: `List.of()`, `Map.of()`, `Collections.unmodifiableList()`.
- Use streams for transformations and filtering. Avoid mutating external state inside a stream.
- Avoid side effects in `map()` or `filter()` — use `forEach()` or a plain loop when mutation is needed.
- Do not use raw types. Always parameterize generics: `List<CrewMember>`, not `List`.

---

## Spring-Specific Standards

- Use constructor injection exclusively. Field injection (`@Autowired` on fields) is not allowed.
- Annotate service classes with `@Service`, repositories with `@Repository`, controllers with `@RestController`.
- Keep controllers thin — no business logic. Controllers translate HTTP to service calls and back.
- Use `@Validated` and JSR-380 annotations (`@NotNull`, `@Size`, `@Min`) on request DTOs.
- Define `@ControllerAdvice` for centralized exception-to-HTTP-status mapping.
- Externalize all configuration to `application.yml`. No hardcoded URLs, credentials, or timeouts in code.

---

## REST API Design

- Use nouns for resource paths, not verbs: `/crew-members`, not `/getCrewMembers`.
- Use standard HTTP methods: `GET` (read), `POST` (create), `PUT` (full replace), `PATCH` (partial update), `DELETE`.
- Return appropriate HTTP status codes: `200 OK`, `201 Created`, `204 No Content`, `400 Bad Request`, `404 Not Found`, `409 Conflict`, `500 Internal Server Error`.
- Version APIs via the path: `/api/v1/crew-members`.
- Return consistent error bodies with `timestamp`, `status`, `error`, and `message` fields.

---

## Security

- Never hardcode credentials, API keys, or secrets. Use environment variables or a secrets manager.
- Validate and sanitize all user input before processing or persisting.
- Use parameterized queries or JPA. Never concatenate user input into SQL or JPQL.
- Apply the principle of least privilege: request only the permissions and roles a feature needs.
- Log authentication and authorization failures at `WARN` level with sufficient context for audit.

---

## Testing Standards

- Every public service method must have at least one unit test covering the happy path and one covering failure.
- Use JUnit 5 (`@Test`, `@BeforeEach`, `@ExtendWith`).
- Use Mockito for mocking dependencies. Do not spin up a Spring context for unit tests.
- Test method names describe the scenario: `assignCrew_whenMemberUnavailable_throwsConflictException`.
- Aim for 80%+ line coverage on `service` and `util` packages. Coverage alone is not quality — test behavior, not implementation.
- Use `@SpringBootTest` sparingly, only for integration tests that need the full context.
- Keep tests independent and idempotent. Tests must not depend on execution order.

---

## Documentation

- Every public class and public method in a shared library or API must have a Javadoc comment.
- Javadoc should explain **why** and **what**, not restate the code.
- Inline comments explain non-obvious decisions. If the code is clear, skip the comment.
- Keep comments current — stale comments are worse than no comments.

---

## SonarQube Compliance

All committed code must pass SonarQube analysis with no new blockers or criticals. Common rules enforced:

- `squid:S1172` — Remove unused method parameters.
- `squid:S1481` — Remove unused local variables.
- `squid:S2095` — Resources must be closed.
- `squid:S1135` — Resolve or remove `TODO` comments before merging.
- `squid:S3776` — Reduce cognitive complexity (max 15 per method).
- `squid:S106`  — Replace `System.out` with a logger.
- `squid:S2259` — Null dereference — check before use.

Run `mvn sonar:sonar` locally before opening a pull request.
