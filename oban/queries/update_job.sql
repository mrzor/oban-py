WITH raw_job_data AS (
    SELECT
        unnest(%(ids)s::bigint[]) AS id,
        unnest(%(args)s::jsonb[]) AS args,
        unnest(%(max_attempts)s::smallint[]) AS max_attempts,
        unnest(%(meta)s::jsonb[]) AS meta,
        unnest(%(priority)s::smallint[]) AS priority,
        unnest(%(queue)s::text[]) AS queue,
        unnest(%(scheduled_at)s::timestamptz[]) AS scheduled_at,
        unnest(%(tags)s::jsonb[]) AS tags,
        unnest(%(worker)s::text[]) AS worker
),
locked_jobs AS (
  SELECT
    id
  FROM
    oban_jobs
  WHERE
    id = ANY(%(ids)s)
  FOR UPDATE
)
UPDATE
  oban_jobs oj
SET
  args = rjd.args,
  max_attempts = rjd.max_attempts,
  meta = rjd.meta,
  priority = rjd.priority,
  queue = rjd.queue,
  scheduled_at = rjd.scheduled_at,
  state = CASE
    WHEN oj.state = 'available' AND rjd.scheduled_at > timezone('UTC', now())
    THEN 'scheduled'::oban_job_state
    WHEN oj.state = 'scheduled' AND rjd.scheduled_at <= timezone('UTC', now())
    THEN 'available'::oban_job_state
    ELSE oj.state
  END,
  tags = rjd.tags,
  worker = rjd.worker
FROM
  raw_job_data rjd
  INNER JOIN locked_jobs lj ON rjd.id = lj.id
WHERE
  oj.id = rjd.id
RETURNING
  oj.args,
  oj.max_attempts,
  oj.meta,
  oj.priority,
  oj.queue,
  oj.scheduled_at,
  oj.state,
  oj.tags,
  oj.worker;
