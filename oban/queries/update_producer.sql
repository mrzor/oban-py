UPDATE oban_producers
SET meta = meta || %(meta)s
WHERE uuid = %(uuid)s
