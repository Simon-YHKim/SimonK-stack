# perspectives.md — {{PROJECT_NAME}}

> Cumulative blind-spot audit. Each session run of `/perspectives` prepends a new block.
> Older blocks below are preserved verbatim.

---

## Session {{DATE}} {{TIME}} — {{ONE_LINE_SUMMARY}}

### Session inventory

- **Files touched**: {{FILES}}
- **Decisions made**: {{DECISIONS}}
- **Skills invoked**: {{SKILLS}}
- **Skipped / deferred**: {{SKIPPED}}

### Core 5 audit

#### User
- **Considered**: {{USER_SEEN}}
- **Missed**: {{USER_GAP}}
- **Severity**: {{USER_SEV}}

#### Business
- **Considered**: {{BIZ_SEEN}}
- **Missed**: {{BIZ_GAP}}
- **Severity**: {{BIZ_SEV}}

#### Technical
- **Considered**: {{TECH_SEEN}}
- **Missed**: {{TECH_GAP}}
- **Severity**: {{TECH_SEV}}

#### Security
- **Considered**: {{SEC_SEEN}}
- **Missed**: {{SEC_GAP}}
- **Severity**: {{SEC_SEV}}

#### Future-self (3 months / 1 year)
- **Considered**: {{FS_SEEN}}
- **Missed**: {{FS_GAP}}
- **Severity**: {{FS_SEV}}

### Session-specific perspectives

#### {{STAKEHOLDER_1}}
- **Why this matters here**: {{S1_WHY}}
- **Missed**: {{S1_GAP}}
- **Severity**: {{S1_SEV}}

{{#STAKEHOLDER_2}}
#### {{STAKEHOLDER_2}}
- **Why this matters here**: {{S2_WHY}}
- **Missed**: {{S2_GAP}}
- **Severity**: {{S2_SEV}}
{{/STAKEHOLDER_2}}

{{#STAKEHOLDER_3}}
#### {{STAKEHOLDER_3}}
- **Why this matters here**: {{S3_WHY}}
- **Missed**: {{S3_GAP}}
- **Severity**: {{S3_SEV}}
{{/STAKEHOLDER_3}}

### Top 3 actionable findings — resolution

| # | Finding | Decision | Notes |
|---|---|---|---|
| 1 | {{FINDING_1}} | {{DECISION_1}} | {{NOTES_1}} |
| 2 | {{FINDING_2}} | {{DECISION_2}} | {{NOTES_2}} |
| 3 | {{FINDING_3}} | {{DECISION_3}} | {{NOTES_3}} |

Decision values: `address-now` / `backlog` / `acknowledge`.

---

<!-- Older session blocks below — do not edit, do not delete -->
