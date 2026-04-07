# PRD Examples

Excerpts from production PRDs demonstrating effective patterns.

## Example 1: Phase II Implementation Plan

Source: Multi-platform upload workflow implementation

### Excellent Thread Structure

```markdown
### 15) Multi-platform post creation — Reasoning Effort: medium ✅ COMPLETED

**Goal**: Create N posts (one per selected platform) from a single upload; share batch_id, unique platform/sequence.

**Acceptance**: Uploading 3 files for LinkedIn + YouTube creates 6 posts total (3 LinkedIn, 3 YouTube); each has correct platform, sequence, video_url.

**Changes**:
- Modify `admin_api/routers/uploads.py` POST handler:
  - Loop over selected platforms
  - For each platform, create posts with platform-specific naming
  - All posts in a batch share `batch_id`, `metricool_id`, `video_url`, `transcript`
  - Sequence numbers restart per platform or continue across platforms (decide based on existing pattern)
- Update filename generation to use platform in canonical pattern (already exists in `file_renamer.py`)
- Update preview endpoint to show platform breakdown

**Read first**: `social_media_pipeline/admin_tool/file_renamer.py:1`, `social_media_pipeline/admin_api/routers/uploads.py:180-250`, `social_media_pipeline/shared/services/db_service.py:1`

**Key Decision**: Sequence numbering
- **Option A**: Restart sequence per platform (LinkedIn_1, LinkedIn_2, LinkedIn_3; YouTube_1, YouTube_2, YouTube_3) ✅ IMPLEMENTED
- **Option B**: Continuous sequence across platforms (LinkedIn_1, LinkedIn_2, LinkedIn_3; YouTube_4, YouTube_5, YouTube_6)
- **Recommendation**: Option A (restart per platform) for clarity; each platform's batch is self-contained
```

### Excellent Completion Log

```markdown
**Completion Log — Step 15**
- Date: 2025-09-30
- **SCHEMA CHANGE**: Added `platform` column to `posts` table (TEXT, nullable, indexed)
- Created migration: `shared/db/migrations/add_platform_to_posts.sql`
- Created migration documentation: `shared/db/migrations/README.md`
- Updated Post ORM model with `platform` field and indexes:
  - `ix_posts_platform` - Platform filtering index
  - `ix_posts_client_platform_status` - Composite index for common queries
- Updated `naming.py` canonical pattern to include platform prefix:
  - Old: `client-{name}__blog-{id}__duration-{sec}sec__batch-{count}__type-{type}__timestamp-{ts}__{original}{ext}`
  - New: `{Platform}__client-{name}__blog-{id}__batch-{count}__seq-{num}__type-{type}__timestamp-{ts}__{original}{ext}`
- Tested with comprehensive test suite (`test_step15_multiplatform.py`):
  - ✅ Schema migration (platform column exists)
  - ✅ Naming pattern (platform prefix correct)
  - ✅ Multi-platform logic (N × M posts)
  - ✅ Preview structure (correct breakdown)
  - ✅ Duplicate detection (platform-specific)
- Verified: No linter errors
- Next step: Step 16 (Remove CTA/hashtag standalone fetching)
```

**Why this works**:
- Specific file:line references for reading
- Clear decision point with recommendation
- Testable acceptance criteria
- Detailed completion log with actual changes

---

## Example 2: Models YAML Source-of-Truth Plan

Source: Configuration management incident response

### Excellent Shared Resources Section

```markdown
## Shared Resources for All Threads

- Repository root: `/path/to/social_media_pipeline`
- Key config file: `config/models.yaml`
- Python config helpers: `caption_service/utils/config.py`, `shared/config/settings.py`
- Service entrypoint & logging: `caption_service/main.py`
- Tests: `social_media_pipeline/tests/` (run with `pytest`)
- Documentation: `docs/guides/MODEL_CONFIGURATION_GUIDE.md`
- Containers: `docker compose exec caption-service ...` (for production-style validation)
```

### Excellent Thread with Model Recommendation

```markdown
### Thread 2 — Config Resolver Refactor ✅ COMPLETED (2025-10-21)

- **Purpose**: Introduce source-aware resolver and logging inside `caption_service/utils/config.py`.
- **Actions**: Implement resolver helper, surface source metadata, wire INFO log in service startup.
- **Reference material**: review `caption_service/utils/config.py` (model constants & `_load_models_config()`), `shared/config/settings.py` (env loading order), and existing logging in `caption_service/main.py`.
- **Validation targets**: `social_media_pipeline/tests/test_bedrock_toggle.py` (imports config constants), new targeted tests under `tests/config/`, manual run of `python -m caption_service.main --show-debug-info` to confirm logging.
- **Deliverables**: Updated resolver (with per-component source metadata), startup INFO log summarizing resolved models, accompanying docstring/comments, passing tests recorded via `pytest`.
- **Output**: PR touching config helper + main entrypoint with unit coverage for resolver.
- **Reasoning effort**: Medium (code comprehension & refactor; Sonnet 3.7/4.0 recommended).

**Implementation Details:**
- ✅ Created `_resolve_model()` and `_resolve_fallback_model()` functions that track resolution source
- ✅ Added `_model_resolution_sources` dict to track which source (env/yaml/default) was used for each model
- ✅ Implemented `get_model_resolution()` function to expose resolution metadata
- ✅ Implemented `format_model_resolution_table()` to create human-readable table output
- ✅ Added startup logging in `caption_service/main.py:initialize_services()` that displays full model configuration table
```

**Why this works**:
- Explicit model recommendation in reasoning effort
- Multiple validation targets
- Reference material describes WHY to read each file
- Implementation details serve as context for future threads

---

## Example 3: Admin Captioning HIL Workflow Plan

Source: Human-in-the-loop captioning workflow

### Excellent Sequential Checklist Format

```markdown
## Sequential Thinking Checklist (One Thread per Step)

Thread 1 — DB migrations — ✅ COMPLETED (2025-01-31)
- ✅ Confirmed current schema (001_initial_migration.py reviewed)
- ✅ Created Alembic migration 002_components_platforms_api_costs_precision_cost_indexes.py
- ✅ Added `components.platforms TEXT[]` with GIN index for array queries
- ✅ Added backfill logic: `UPDATE components SET platforms = ARRAY[platform]`
- ✅ Added platform consistency check constraint
- ✅ Changed `api_costs.cost_usd` to NUMERIC(10,4) for currency precision
- ✅ Added indexes: `ix_api_costs_model`, `ix_api_costs_operation`
- ✅ Rollback plan implemented in downgrade() function
- ✅ Migration guide created: MIGRATION_GUIDE.md
- 📋 Ready for application: `alembic upgrade head`

Thread 2 — ORM/service parity — ✅ COMPLETED
- ✅ Updated shared/db/models.py: Added `platforms` TEXT[] to Component
- ✅ Added GIN index on Component.platforms
- ✅ Updated NotionCompatService.get_pipeline_component to prefer platforms[]
- ✅ Verified models import correctly and service initializes without errors

Thread 3 — Captions HIL — ✅ COMPLETED
- ✅ Added `/notes` and `/recaption` endpoints with validation
- ✅ Save notes → persisted in `feedback_summary`, timestamp bumps
- ✅ Recaption requires non‑empty notes; sets status correctly
```

**Why this works**:
- Clear status indicators (✅, 📋, ⬜)
- Actionable completion items
- Serves as context for subsequent threads
- Date stamps for tracking

---

## Example 4: Execution Instructions Block

Include this in every PRD so executing agents know the protocol:

```markdown
## How to Execute Threads

1. Read this PRD fully before starting
2. Execute ONE thread per conversation
3. Start your thread by stating: "Executing Thread N: [Name]"
4. Read all reference material listed for the thread
5. Complete all actions and validation targets
6. Update the PRD with completion log before ending
7. State: "Thread N complete. Next: Thread N+1"
```

---

## Anti-Patterns to Avoid

### Vague References

❌ Bad:
```markdown
- **Reference material**: Check the config files and the service code
```

✅ Good:
```markdown
- **Reference material**:
  - `caption_service/utils/config.py:84` - current model loading
  - `shared/config/settings.py:13-25` - env var precedence
```

### Missing Acceptance Criteria

❌ Bad:
```markdown
### Thread 3 — Add platform support
- **Actions**: Update the code to support platforms
```

✅ Good:
```markdown
### Thread 3 — Add platform support — Reasoning Effort: medium
- **Actions**: Add platform column, update queries, modify templates
- **Acceptance**: Uploading for 2 platforms creates 2× posts; each has correct platform field
- **Validation**: Query shows `SELECT platform, count(*) FROM posts GROUP BY platform`
```

### Scope Creep

❌ Bad:
```markdown
### Thread 2 — Add filter and also fix the styling and maybe refactor the query
```

✅ Good:
```markdown
### Thread 2 — Add platform filter to posts page — Reasoning Effort: low
### Thread 3 — Update posts page styling — Reasoning Effort: minimal
### Thread 4 — Refactor posts query for performance — Reasoning Effort: medium
```

### Missing Model Recommendation

❌ Bad:
```markdown
- **Reasoning effort**: medium
```

✅ Good:
```markdown
- **Reasoning effort**: Medium (code comprehension & refactor; Sonnet recommended)
```
