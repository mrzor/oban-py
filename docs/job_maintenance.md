# Job Maintenance

Oban stores all jobs in the database, which offers several advantages:

- **Durability**: Jobs survive application restarts and crashes
- **Visibility**: Administrators can inspect job status and history
- **Accountability**: Complete audit trail of job execution

## Pruning Jobs

Oban automatically prunes `completed`, `cancelled`, and `discarded` jobs after a configurable
period (1 day, by default) to prevent the table from growing indefinitely. A pruner periodically
runs in the background to delete jobs that are in a final state and have exceeded the retention
period.

### Configuring Pruning

You can customize pruning behavior in `oban.toml`:

```toml
[pruner]
max_age = 3_600 # Keep jobs for 1 hour
limit = 50_000  # Delete up to 50k jobs per run
```

Or programmatically when running embedded:

```python
oban = Oban(
    pool=pool,
    queues={"default": 10},
    pruner={"max_age": 3_600, "limit": 50_000}
)
```

## Rescuing Jobs

During deployment or unexpected restarts, jobs may be left in an executing state indefinitely. We
call these jobs "orphans", but orphaning isn't a bad thing. It means that the job wasn't lost and
it may be retried again when the system comes back online.

The "lifeline" process automatically rescues orphaned jobs by periodically checking for jobs stuck
in the `executing` state and moving them back to `available` so they can run again.

**Lifeline is enabled by default** and runs every 60 seconds.

### Configuring Lifeline

You can customize the check interval in `oban.toml`:

```toml
[lifeline]
interval = 30  # Check for orphaned jobs every 30 seconds
```

Or programmatically when running embedded:

```python
oban = Oban(
    pool=pool,
    queues={"default": 10},
    lifeline={"interval": 30}
)
```

## Guidelines

* Pruning is best-effort and performed out-of-band. This means that all limits are soft; jobs
  beyond a specified age may not be pruned immediately after jobs complete.

* Pruning is only applied to jobs that are `completed`, `cancelled`, or `discarded`. It'll never
  delete jobs in an incomplete state.

* For high-volume systems, consider reducing `max_age` to keep the jobs table smaller, or
  increasing `limit` to prune more jobs per run.

* The lifeline process rescues jobs that appear to be stuck, allowing them to be retried. This
  prevents jobs from being lost due to unexpected crashes or deployments.
