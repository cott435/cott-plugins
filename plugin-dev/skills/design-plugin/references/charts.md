# The charts and the page

The charts are how the user checks that the design understood the point. Each one must be
readable at a glance and must match every other chart and the components table.

## Which charts

- **One chart per workflow**, a `mermaid` `flowchart TB`: the trigger → what the orchestrator
  decides → the loops it runs, with fan-out shown as such (`claim-reader ×N`) → the files
  written → the next reader, and the deliverable. An evaluator appears as a node with a
  labelled edge back to the producer (`reject`). Under it, a caption of three lines:
  **Unit** (what one instance reads and writes), **Strengthened by**, and **Inputs from**
  (each input the unit needs and who supplies it).
- **One system chart**, drawn after the workflow charts: every loop as one node or one
  `subgraph`, the typed commands, and the files where loops meet. Nothing else goes in it. It
  answers "how do these fit together", and a file that one workflow writes and another reads
  is the most important thing it shows.

## Keeping them legible

A chart past about 20 nodes and 30 edges is a wiring diagram nobody reads. One early chart
drew 31 nodes and 55 edges and came out nearly four thousand pixels wide. To stay inside the
limit:

- Use one node per typed command and per agent, each exactly once per chart. An agent with two
  modes is one node with its edges labelled by mode.
- Use one node per shared file, and one node per set of per-unit files (`claims/*.md`), not one
  per instance. A report nobody else reads can be the command's edge label.
- Knowledge skills and scripts go in the components table, not the chart. An agent's preloaded
  skills can be a second line in its label.
- A hook is drawn only where it guards something: a small node on the edge it gates, labelled
  with its event (`PreToolUse`). An MCP server is a source node the agents that use it read
  from, drawn once.
- Keep edge labels to a word or two, because long labels widen a chart more than anything else.
- Use the same node ID and label for a component in every chart it appears in, so the reader
  can match them across charts.

## Styling

Suggestions are dashed (`classDef suggested stroke-dasharray:5 5`). In **change** mode, nodes
carry `classDef new` or `changed`, or are left unmarked when unchanged; a removed node is shown
struck with `classDef removed`. Nothing appears in any chart that is not in the components
table.

## The components table

This table goes on the page below the charts, with these columns: Name · Kind (agent, workflow
skill, forked skill, knowledge skill, hook, MCP server, script, config) · Role · Reads · Writes · Used by (the workflows that depend on
it) · Origin. Origin is one of:

- *asked*: an answer names it;
- *composed*: the loops need it to serve what was asked;
- *suggested: why*: optional, and the user accepts or rejects it.

Label honestly. A component nobody asked for is not *asked*.

## The page

When the session has the `Artifact` tool, the charts are published as an Artifact, an HTML
page that follows that tool's own rules. Each chart goes in a `<pre class="mermaid">` block
inside a container styled `overflow-x: auto`. The page must also read correctly as a plain
file, so:

- open it with `<meta charset="utf-8">`. The Artifact viewer adds one, but a downloaded file
  has none, and without it every dash turns to mojibake;
- have it load mermaid itself, with
  `<script src="https://cdnjs.cloudflare.com/ajax/libs/mermaid/11.15.0/mermaid.min.js"></script>`
  at the end of the body, followed by an initializer that matches the viewer's theme and keeps
  each chart at full size:

```html
<script>
const t = document.documentElement.dataset.theme;
const dark = t ? t === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
mermaid.initialize({startOnLoad: true, theme: dark ? "dark" : "default",
                    flowchart: {useMaxWidth: false}});
</script>
```

The charts then render the same when the file is downloaded or opened locally, and a wide
chart scrolls instead of shrinking its text to nothing.

Write the page in the session scratchpad and republish the same file path after every
revision, so the link stays the same. The page is also the draft's memory: if the conversation
is compacted mid-design, read the page back with the `Artifact` tool before continuing.

Without the `Artifact` tool, use whatever tool the session has for showing a rendered diagram.
Only when there is none, put the `mermaid` blocks in chat.
