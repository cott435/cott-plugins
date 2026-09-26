# Composing the workflows

The interview gives you jobs: the things the user will type. This reference turns jobs into
a design: the loops that do the work, what each loop's unit is, what makes each unit's output
trustworthy, where every input a unit needs comes from, and the files where the loops meet.
The charts draw exactly what this produces, so nothing here is optional.

## The design this exists to prevent

The easy design gives each job its own command and its own agent: three jobs, three agents,
each starting from scratch. It is shallow in every job (no agent goes deep when it must also
do everything else), repeats the same work in each, has nothing to run in parallel, and has
no loop that a second loop feeds. It hands the user's own list back to them without expanding
it. A 1:1 match between agents and commands is the sign that composing has not happened yet.

## The method

Work through it per workflow, then across workflows. Write the answers down as you go; they
are the chart captions and, later, the writeup's **Workflows** section.

1. **Name the workflows.** A workflow is a job from its trigger (the user types something, a
   file lands) to its deliverable (a report, an edit, a decision). Name each in the user's
   words, with its trigger and its deliverable.

2. **Find the unit of work.** The smallest piece where a judgment is made that a practitioner
   would make one at a time: one clause of a contract, one endpoint of an API, one interview
   transcript. Name the unit's source (what it reads), its output file, and the fields of that
   file. This is where depth lives, and it is the grain of an agent that runs as many parallel
   instances, one per unit.
   - Too big: the agent must "read everything" or "analyze the whole set". Split it until one
     instance reads one thing.
   - Too small: the step only counts, filters, sorts or dedupes. That is a script, not an
     agent.

3. **Make the unit strong.** Ask what goes wrong when one unit's output is wrong, and pick what
   prevents it:
   - **structure**: required fields that force the work (every finding carries the line it
     came from; every judgment names what it was judged against);
   - **an evaluator**: a second agent, in its own context, that checks the unit's output
     against the same source and returns accept or a specific rejection. The producer does not
     grade itself;
   - **a revision loop**: a rejection goes back to the producer with the evaluator's reasons,
     capped at a stated number of rounds, after which the unit is marked unresolved rather
     than retried forever;
   - **rules of what it must never claim**: see step 10.

   A unit whose output others build on nearly always earns an evaluator. Say why when one does
   not.

4. **List what the unit needs decided before it runs.** Every unit has inputs besides its
   source: *which* units to run on, *what* to look for in each, *what* to judge against. For
   each input, name who supplies it:
   - **the user**: an argument, a config file they edit. Done.
   - **a file already on disk**, written by some other loop. Link the two.
   - **neither.** Then something must produce it, and that something is another loop. It
     usually needs to be wider and cheaper than the loop it feeds: it touches every candidate
     lightly so the expensive loop can touch a few deeply. Name the orchestrator that makes the
     decision (usually a workflow skill) and the file it decides from.

   An input that changes what the unit extracts, such as a question, a focus or a policy,
   makes the unit's output specific to that input. Then the output file records the input it
   was produced for, and the orchestrator that chooses the input needs something to choose
   from.

5. **Repeat step 4 on every loop it created** until every input is supplied by the user or
   read from disk. The result is a small graph of loops. Two or three loops feeding each other
   is normal for a plugin worth planning in phases; one loop per job with nothing between them
   usually means step 4 was skipped.

6. **Find what the workflows share.** Line the workflows up. Any loop or file two of them
   would each derive is built once, written to a file, and read by both. Agents are methods and
   workflow skills are orchestrations: an agent is one way of working done expertly, shared by
   every workflow that needs that method; a workflow skill decides which loops to run or
   refresh, in what order, and how wide to fan out.

7. **Integrate at files.** Every place two loops meet is a file. For each, name its path, the
   loop that writes it, every reader, the fields the readers depend on, and what it records
   about its own freshness (what it was built from, when). A reader rebuilds a file only when
   its inputs changed, and that is what makes running a workflow across many entities
   affordable.

8. **Tier the cost.** For each loop, estimate how many units it covers, how deep it reads each,
   and what a cold run reads compared with a warm one once the files exist. Cheap, wide loops
   feed expensive, narrow ones. Spend depth where the judgment is made. Default every horizon
   (how far back, how many items) to the least the question needs; a longer one is the user's
   call.

9. **Judge relative to something.** A practitioner's judgment is always against a baseline:
   peers, the rest of the field, the cohort, last period, a policy. For every judgment the
   design makes, name its baseline and the loop or file that provides it. This is part of the
   core design, not a suggestion. Leave it out only when the thing judged genuinely has no peer
   or baseline, and say so in the design.

10. **Say what each output must say.** For every file a reader depends on, name its sections
    and the domain rules that make it trustworthy: what it must cite, what it must never claim,
    and when it goes stale. Structure without those rules produces well-organized files nobody
    can rely on.

11. **Walk it as the practitioner would.** Go through each workflow as the domain's
    professional and name what they would insist on that no component does: a check before
    anything irreversible, a critic for a synthesis. Each one becomes a **suggestion**, named
    with one line of why. A suggestion attaches to the design and never carries it: no
    component the user asked for reads a suggestion's file, and nothing in the core depends on
    it. Rejecting any suggestion removes that component and nothing else.

## Shapes that recur

These come up often. Use one because steps 2 to 9 derived it, never because it is on the list.

- **Fan-out.** One agent instance per unit, in parallel, each writing one file.
- **Survey, select, go deep.** A cheap pass over every candidate writes an index; an
  orchestrator reads the index and chooses which candidates get the expensive pass, and with
  what input.
- **Produce, evaluate, revise.** An evaluator in its own context, a capped revision loop.
- **Synthesize per entity.** One agent reads every unit file about one entity and writes that
  entity's current state, the file everything above it reads.
- **Compare.** The entity against its baseline (step 9).
- **Thin job.** The typed command composes files that already exist, plus whatever only it
  needs, and answers its question.

## Before the charts are drawn

- For each workflow, the unit, what strengthens it, and every input's supplier are named.
- Every file is named along with its writer and readers. At least one file is read by more
  than one workflow, or the design says why none is.
- Every fan-out states what it fans out over and how many instances; its arithmetic adds up
  (batch size × batches covers the units).
- Every judgment names its baseline.
- With every suggestion removed, the core still works end to end.
- The depth is the same everywhere it is described: a source is not "read in full" in one
  place and "skimmed" in another.

Anything only the user can settle (how many entities, how far back) is asked as one more
interview round before the charts, not assumed on them.
