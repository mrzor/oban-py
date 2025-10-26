DELETE FROM
  oban_jobs
WHERE
  id = ANY(%(ids)s)
  AND state != 'executing'
