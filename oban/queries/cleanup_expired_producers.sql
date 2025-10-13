DELETE FROM oban_producers
WHERE updated_at < timezone('UTC', now()) - make_interval(secs => %(max_age)s)
