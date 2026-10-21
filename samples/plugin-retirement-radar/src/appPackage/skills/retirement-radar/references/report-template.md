# Retirement Radar report template

**Verdict:** {N} of {M} Microsoft dependencies need action - {X} are already retired.

| # | Finding | Where in your code | Status | Official date | Replacement | Source |
|---|---|---|---|---|---|---|
| 1 | {technology} | line {n}: `{snippet}` | Broken now / Breaking soon / Deprecated / OK | {date exactly as in docs} | {replacement} | [{doc title}]({learn url}) |

## Fixes

### 1. {technology} -> {replacement}
Before:
```{language}
{original lines}
```
After:
```{language}
{rewritten lines, based on the official sample}
```
Why: {one sentence quoting or paraphrasing the Learn doc}.

## Migration checklist
1. [ ] Broken now: {item} - {first concrete step}
2. [ ] Breaking soon: {item}
3. [ ] Deprecated: {item}

_All dates and replacements verified against Microsoft Learn on {today's date}._
