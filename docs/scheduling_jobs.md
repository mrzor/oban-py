# Scheduling Jobs

Oban provides flexible options to schedule jobs for future execution. This is useful for scenarios
like delayed notifications, periodic maintenance tasks, or scheduling work during off-peak hours.

## Schedule in Relative Time

You can schedule jobs to run after a specific delay using the `schedule_in` parameter:

```python
from datetime import timedelta

# Using timedelta
await MyWorker.enqueue({"id": 1}, schedule_in=timedelta(seconds=5))

# Or using seconds directly
await MyWorker.enqueue({"id": 1}, schedule_in=5)
```

This is useful for tasks that need to happen after a short delay, such as sending a follow-up
email or retrying a failed operation.

## Schedule at a Specific Time

For tasks that need to run at a precise moment, you can schedule jobs at a *specific timestamp*
using the `scheduled_at` parameter:

```python
await MyWorker.enqueue({"id": 1}, scheduled_at=some_datetime)
```

This is particularly useful for time-sensitive operations like executing a maintenance task at
off-hours, or preparing monthly reports.

## Time Zone Considerations

Scheduling in Oban is *always* done in UTC. If you're working with timestamps in different time
zones, you should convert them to UTC before scheduling:

```python
from datetime import timezone

utc_time = local_datetime.astimezone(timezone.utc)

await MyWorker.enqueue({"id": 1}, scheduled_at=utc_time)
```

This ensures consistent behavior across different server locations and prevents daylight saving
time issues.

## How Scheduling Works

Behind the scenes, Oban stores your job in the database with the specified scheduled time. The job
remains in a `scheduled` state until that time arrives, at which point it becomes `available` for
execution by the appropriate worker.

Scheduled jobs don't consume worker resources until they're ready to execute, allowing you to
queue thousands of future jobs without impacting current performance.
