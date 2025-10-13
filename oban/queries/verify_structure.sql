SELECT
  table_name
FROM
  information_schema.tables
WHERE
  table_schema = %(prefix)s
  AND table_name = ANY('{oban_jobs,oban_leaders,oban_producers}')
ORDER BY
  table_name
