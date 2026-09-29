# `docs/packages/<pkg>/changes/<slug>.md` — a change file

Written by the architect when an edit touches a built or shipped package (CHANGE outcome);
read by `status.py` (re-opens the named sections at DESIGN while `Status: open`), the designer
(`delta` mode), the implementer, the reviewer, and `sync-plan`, which applies it to the
canonical contracts and sets `Status: synced`. Budget 120 lines. The slug is one lowercase
token; the file is history once synced and is never edited afterwards except for that line.
One file per affected package: a repo-level change (from `/dev-team:plan-repo`) writes one
file per package it touches, all with the same slug, each naming only that package's sections
under **Affected sections** and only that package's groups under **Contract changes** plus the
**Repo contract** group when the change touches it. A `docs/changes/<slug>.md` from before 2.2
is still read as naming every package its Affected sections name, and is synced where it is.

The line after the title is `Status: open | synced`.

1. **Change goal** — one paragraph.
2. **Affected sections** — qualified `<pkg>/<section>` names of this package only, one line each with what changes
   for it, including the consumer sections this change adapts.
3. **Contract changes** — grouped **Repo contract** (when touched), **Package contract: <pkg>**
   (this package), **Interface: <pkg>** (when its shipped surface is altered); Added / Changed / Removed
   within each. Every altered shipped name with its old and new signature.
4. **Downstream impact** — table: consumer | shipped or planned | names affected | what breaks.
   Consumers from the grep `sync-plan` and the architect share (`from <pkg>\b|import <pkg>\b`
   over `packages/*/src`, plus every contract whose **Consumes** names the package).

Never claims a change to a canonical contract: the contracts are edited by `sync-plan` once
the sections are DONE, never here.
