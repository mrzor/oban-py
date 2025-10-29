WITH params AS (
  SELECT unnest(%(id)s::bigint[]) AS id,
         unnest(%(state)s::oban_job_state[]) AS state,
         unnest(%(attempt_change)s::integer[]) AS attempt_change,
         unnest(%(schedule_in)s::int[]) AS schedule_in,
         unnest(%(error)s::jsonb[]) AS error,
         unnest(%(meta)s::jsonb[]) AS meta
),
locked AS (
  SELECT oj.id
  FROM oban_jobs oj
  INNER JOIN params tmp ON oj.id = tmp.id
  WHERE oj.state = 'executing'
  FOR UPDATE OF oj
)
UPDATE oban_jobs oj
SET state = tmp.state,
    cancelled_at = CASE WHEN tmp.state = 'cancelled' THEN timezone('UTC', now()) ELSE oj.cancelled_at END,
    completed_at = CASE WHEN tmp.state = 'completed' THEN timezone('UTC', now()) ELSE oj.completed_at END,
    discarded_at = CASE WHEN tmp.state = 'discarded' THEN timezone('UTC', now()) ELSE oj.discarded_at END,
    scheduled_at = CASE WHEN tmp.schedule_in IS NULL THEN oj.scheduled_at ELSE timezone('UTC', now()) + make_interval(secs => tmp.schedule_in) END,
    attempt = COALESCE(tmp.attempt_change + oj.attempt, oj.attempt),
    errors = CASE WHEN tmp.error IS NULL THEN oj.errors ELSE oj.errors || tmp.error END,
    meta = CASE WHEN tmp.meta IS NULL THEN oj.meta ELSE oj.meta || tmp.meta END
FROM params tmp
INNER JOIN locked l ON tmp.id = l.id
WHERE oj.id = tmp.id

