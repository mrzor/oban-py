# Unique Jobs

Uniqueness allows you to specify constraints to prevent *enqueuing* duplicate jobs. These
constraints only apply when jobs are inserted. Uniqueness has no bearing on whether jobs are
*executed* concurrently.

Uniqueness is based on a combination of job attributes using the following options:

* **period** — The number of seconds until a job is no longer considered duplicate Without a
  period, uniqueness will default to `None`, where jobs are unique as long as they're retained in
  the database.

* **fields** — The fields to compare when evaluating uniqueness. The available fields are `args`,
  `queue`, `worker`, and `meta`. Defaults to `["worker", "queue", "args"]`. It's recommended that
  you leave the default fields, otherwise you risk unexpected conflicts between unrelated jobs.

* **keys** — A specific subset of the `args` or `meta` to consider when comparing against historic
  jobs. This allows a job with multiple key/value pairs in its arguments to be compared using only a
  subset of them.

* **group** — A group of job states that are checked for duplicates. The available named groups
  are:

  * `all` - All states
  * `incomplete` - Jobs that haven't completed processing
  * `scheduled` - Only scheduled jobs (useful for "debouncing")
  * `successful` - Jobs that aren't cancelled or discarded (the default)

## Configuring Uniqueness

The simplest form of uniqueness using default settings is to set unique to `True`:

```python
from oban import worker

@worker(queue="default", unique=True)
class MyWorker:
    async def process(self, job):
        pass
```

You can also specify a period to limit how long jobs are considered duplicates:

```python
# Jobs are unique for 5 minutes
await MyWorker.enqueue({"id": 1}, unique={"period": 300})
```

Here's a more complex example which uses multiple options:

```python
@worker(unique={
        # Jobs should be unique for 2 minutes
        "period": 120,
        # Don't consider the whole args field, just the url key within args
        "keys": ["url"],
        # Consider a job unique across all states, including cancelled/discarded
        "group": "all",
        # Consider a job unique across queues; only compare the worker and url key
        "fields": ["worker", "args"],
    }
)
```

## Uniqueness vs Concurrency

It's important to understand the distinction between uniqueness and concurrency. While these
concepts may seem related, they operate at different stages of a job's lifecycle.

Uniqueness operates at **job insertion time**. When a job is marked as unique, Oban uses a
unique constraint to enforce that only one exists in the database at one time.

* **When it applies** - During job insertion
* **What it prevents** - Duplicate jobs from being inserted
* **What it doesn't affect** - Which jobs run concurrently

A common misunderstanding is that unique jobs run one at a time or in sequence. This isn't
true—uniqueness only prevents duplicate insertions. Once unique jobs are in the queue, they'll run
according to the queue's concurrency settings.

For example, given the following configuration that allows 10 concurrent email jobs:

```toml
[queues]
emails = 10
```

These 10 unique jobs could all run concurrently:

```python
jobs = [
    EmailWorker.new({"user_id": id}, unique=True)
    for id in range(1, 11)
]

await oban.insert_all(jobs)
```

To restrict the number of jobs that run at once you must set concurrency accordingly.

## Detecting Conflicts

When unique settings match an existing job, the return value of `insert()` is still a Job instance.
However, you can detect a unique conflict by checking the job's `conflicted` field. If there was an
existing job, the field is `True`; otherwise it is `False`.

You can use the `conflicted` field to customize responses after insert:

```python
job = await oban.insert(MyWorker.new({"id": 1}, unique=True))

if job.conflicted:
    # Job already exists, handle accordingly
    print("Job already exists")
else:
    # New job was inserted
    print(f"Job inserted with ID: {job.id}")
```

## Specifying Fields and Keys

The `fields` option determines which high-level job attributes Oban will consider when
checking for uniqueness, including `args`, `queue`, `worker`, and `meta`.

When `args` or `meta` are included in the `fields` list, the `keys` option provides additional
specificity by allowing you to designate particular keys within the dictionary for comparison,
rather than comparing the entire args dictionary.

Let's see this with an example:

```python
# This compares the entire args dictionary
await MyWorker.enqueue(
    {"url": "...", "user_id": 1},
    unique={"fields": ["worker", "queue", "args"]}
)

# This compares only the url key within the args dictionary
await MyWorker.enqueue(
    {"url": "...", "user_id": 1},
    unique={"keys": ["url"], "fields": ["worker", "queue", "args"]}
)
```

In the second example, the uniqueness check only looks at the `url` key within the `args` dictionary
because `keys` is specified. Jobs with the same `url` but different `user_id` values would be
considered duplicates.
