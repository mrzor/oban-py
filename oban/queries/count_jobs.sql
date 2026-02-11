SELECT
  state::text,
  queue,
  COUNT(*)::integer
FROM
  oban_jobs
WHERE
  state IN ('available', 'cancelled', 'completed', 'discarded', 'executing', 'retryable', 'scheduled')
GROUP BY
  state, queue
