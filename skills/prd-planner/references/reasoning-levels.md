# Reasoning Levels Guide

Match model capability to task complexity to optimize token usage and cost.

## Level Definitions

### Minimal — Haiku Recommended

**Characteristics**:
- Procedural tasks with clear steps
- Well-documented patterns to follow
- Single file modifications
- No architectural decisions
- Copy-paste with minor adjustments

**Examples**:
- Adding a column to a template
- Updating configuration values
- Documentation updates
- Adding help text to UI
- Creating migration files from existing patterns

**Thread example**:
```markdown
### Thread 1 — Add platform column to CSV export — Reasoning Effort: minimal
- **Purpose**: Include platform field in CSV download
- **Actions**: Add 'platform' as first column in CSV export function
- **Reference material**: `admin_api/routers/uploads.py:430-475`
- **Validation**: Download CSV, verify platform column exists
```

---

### Low — Haiku or Sonnet Recommended

**Characteristics**:
- Clear existing patterns to follow
- Limited decision points
- 2-3 files to modify
- Some comprehension needed but path is clear
- Validation is straightforward

**Examples**:
- Adding a filter to an existing list page
- Creating an endpoint following existing patterns
- Adding indexes to database tables
- Template modifications with existing styling
- Running and validating migrations

**Thread example**:
```markdown
### Thread 3 — Add platform filter to posts page — Reasoning Effort: low
- **Purpose**: Enable filtering posts by platform
- **Actions**:
  - Add platform query parameter to router
  - Add dropdown to template
  - Wire filter to query
- **Reference material**:
  - `admin_api/routers/posts.py:25-95`
  - `admin_api/templates/posts.html:1`
- **Validation**: Filter by platform, verify results match
```

---

### Medium — Sonnet Recommended

**Characteristics**:
- Code comprehension required
- Refactoring existing logic
- Integration between components
- Multiple valid approaches (but guidance given)
- Test coverage needed

**Examples**:
- Service layer refactoring
- Adding new API endpoints with business logic
- Implementing config resolver with source tracking
- Multi-file template enhancements
- Creating test suites for new functionality

**Thread example**:
```markdown
### Thread 2 — Config Resolver Refactor — Reasoning Effort: medium
- **Purpose**: Track model resolution source (env/yaml/default)
- **Actions**:
  - Implement _resolve_model() with source tracking
  - Add get_model_resolution() function
  - Wire INFO log at startup
- **Reference material**:
  - `caption_service/utils/config.py:84` (current loading)
  - `shared/config/settings.py:13` (env loading order)
- **Validation**: Unit tests pass, startup shows resolution table
- **Deliverables**: Updated resolver with tests
```

---

### Medium-High — Sonnet or Opus Recommended

**Characteristics**:
- Architecture decisions required
- Test orchestration complexity
- Cross-cutting concerns
- Policy implementation
- CI/CD integration

**Examples**:
- Implementing override policy with fail-fast
- Test coverage expansion with fixtures
- CI lint rules for deployment hygiene
- Multi-platform component logic
- Monitoring and alerting setup

**Thread example**:
```markdown
### Thread 4 — Test Coverage Expansion — Reasoning Effort: medium-high
- **Purpose**: Ensure CI fails when YAML drift occurs
- **Actions**:
  - Organize test package with shared fixtures
  - Add coverage-enabled runner script
  - Create comprehensive test scenarios
- **Reference material**:
  - `tests/test_bedrock_toggle.py` (existing patterns)
  - `tests/config/` (target location)
- **Validation**: pytest runs, coverage report includes config paths
- **Deliverables**: Test modules, fixtures, documentation
```

---

### High — Opus Recommended

**Characteristics**:
- Novel problem solving
- System design decisions
- Complex debugging across components
- Significant architectural changes
- Security-sensitive implementations

**Examples**:
- Designing new subsystem architecture
- Debugging production incidents
- Implementing authentication/authorization
- Data migration with transformation logic
- Performance optimization requiring profiling

**Thread example**:
```markdown
### Thread 8 — Retrospective Validation — Reasoning Effort: high
- **Purpose**: Verify effectiveness post-rollout and establish monitoring
- **Actions**:
  - Analyze production logs for drift patterns
  - Design recurring validation process
  - Create alerting rules for unexpected models
- **Reference material**:
  - Production logs
  - Threads 2-6 outputs
- **Validation**: Report identifies any gaps, alerts fire correctly
- **Deliverables**: Validation report, runbook updates, alert definitions
```

---

## Decision Framework

Use this flowchart to determine reasoning level:

```
Is this a single-file, procedural change?
├── YES → Minimal
└── NO ↓

Are there existing patterns to follow exactly?
├── YES → Low
└── NO ↓

Does it require understanding code flow across files?
├── YES ↓
│   Is there architecture/policy design involved?
│   ├── YES → Medium-High or High
│   └── NO → Medium
└── NO → Low
```

## Cost Optimization Tips

1. **Batch minimal tasks** - Group several minimal tasks into one thread if they're related
2. **Front-load research** - Use one medium thread to investigate, then several low threads to implement
3. **Isolate high reasoning** - Keep complex decisions in dedicated threads, not mixed with implementation
4. **Document decisions upstream** - Reduce downstream thread complexity by pre-documenting choices in the PRD header

## Model Selection Quick Reference

| Model | Best For | Avoid For |
|-------|----------|-----------|
| **Haiku** | Templates, config, docs, simple CRUD | Refactoring, debugging, design |
| **Sonnet** | Comprehension, integration, testing | Novel architecture, complex debugging |
| **Opus** | Design, debugging, security, novel problems | Simple changes (wasteful) |
