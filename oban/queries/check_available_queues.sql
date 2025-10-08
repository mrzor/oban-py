SELECT
  DISTINCT queue
FROM
  oban_jobs
WHERE
  state = ANY('{available,scheduled,retryable}')
  AND scheduled_at <= timezone('utc', now())
