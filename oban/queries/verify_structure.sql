SELECT
  table_name
FROM
  information_schema.tables
WHERE
  table_schema = %(prefix)s
  AND table_name = ANY('{oban_jobs,oban_leaders}')
ORDER BY
  table_name
