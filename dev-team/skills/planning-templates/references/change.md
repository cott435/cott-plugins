# `docs/changes/<slug>.md` — a change file

Written by the architect when an edit touches a built or shipped package (CHANGE outcome);
read by `status.py` (re-opens the named sections at DESIGN while `Status: open`), the designer
(`delta` mode), the implementer, the reviewer, and `sync-plan`, which applies it to the
canonical contracts and sets `Status: synced`. Budget 120 lines. The slug is one lowercase
token; the file is history once synced and is never edited afterwards except for that line.

The line after the title is `Status: open | synced`.

1. **Change goal** — one paragraph.
2. **Affected sections** — qualified `<pkg>/<section>` names, one line each with what changes
   for it, including the consumer sections this change adapts.
3. **Contract changes** — grouped **Repo contract**, **Package contract: <pkg>** (one per
   package), **Interface: <pkg>** (one per shipped surface altered); Added / Changed / Removed
   within each. Every altered shipped name with its old and new signature.
4. **Downstream impact** — table: consumer | shipped or planned | names affected | what breaks.
   Consumers from the grep `sync-plan` and the architect share (`from <pkg>\b|import <pkg>\b`
   over `packages/*/src`, plus every contract whose **Consumes** names the package).

Never claims a change to a canonical contract: the contracts are edited by `sync-plan` once
the sections are DONE, never here.
