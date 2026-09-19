# Desktop architecture

The supported runtime is a single native CustomTkinter process using SQLite. It
starts no HTTP server and uses no authentication cookie or desktop-login handoff.

`desktop_app → native views → PracticeService / AuthService / desktop_storage → repositories → SQLite`

## Commit boundary

`PracticeService` opens `BEGIN IMMEDIATE`, reads the durable active session, applies
one action to private dataclass instances, and writes the new snapshot. If a round
finishes, `GameService.finalize_round` uses the same context-local connection for
result, progress, review, totals and completion receipt. Repository calls do not
commit independently while a transaction is active. Errors roll back the entire
action. The UI reloads persisted state after successful actions.

Each GameRound carries a stable UUID. A unique completion receipt records the
outcome; repeated completion returns that result without repeating counter updates.
Guesses include the expected round UUID so stale UI events cannot target a new round.
SQLite writer serialization prevents simultaneous duplicate finalization. The desktop
also holds an OS file lock so a second supported process cannot replace its database.

Active practice snapshots are versioned JSON, not pickle. Completed learning cards
and the selected next round are included, so restart works between rounds too.
Time spent with Practice open is accumulated using a monotonic clock; paused and
closed time is excluded. Abrupt process termination can lose the time since the last
submitted action, but not previously saved guesses/results.

## Upgrade and restore

Schema version 1 adds active_practice and completion_receipts to the legacy schema.
Upgrades copy the source into a staging database, retain a pre-upgrade backup, apply
legacy additive migrations and the new schema, verify integrity/foreign keys, then
atomically replace the source. Newer schema versions are rejected. Normal desktop
startup does not reseed the legacy word banks.

Restore rejects invalid databases and unsupported schemas, stages/upgrades the backup,
and saves the previous live database before replacement. The desktop owns the database
exclusively; using a legacy server against the same database simultaneously is unsupported.

## Scope and boundaries

The native UI is split into authentication, practice, reports and settings/help views.
Legacy services remain for regression compatibility; the old home_page is not loaded
by the desktop. The curated service filters new practice to `desktop-core` words while
preserving older rows for historical results. The installer bundles only the native
import graph, CustomTkinter resources and starter content.

Reports derive metrics directly from completed game rows, avoiding reliance on a
possibly stale materialised performance summary. New desktop features should use
PracticeService rather than invoking low-level completion/snapshot APIs separately.
