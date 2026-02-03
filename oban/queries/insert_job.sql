WITH inserted AS (
    INSERT INTO oban_jobs(
        args,
        inserted_at,
        max_attempts,
        meta,
        priority,
        queue,
        scheduled_at,
        state,
        tags,
        worker
    ) VALUES (
        %(args)s,
        coalesce(%(inserted_at)s, timezone('UTC', now())),
        %(max_attempts)s,
        %(meta)s,
        %(priority)s,
        %(queue)s,
        coalesce(%(scheduled_at)s, timezone('UTC', now())),
        CASE
            WHEN %(state)s = 'available' AND %(scheduled_at)s IS NOT NULL
            THEN 'scheduled'::oban_job_state
            ELSE %(state)s::oban_job_state
        END,
        %(tags)s,
        %(worker)s
    )
    RETURNING id, inserted_at, queue, scheduled_at, state
)
SELECT id, inserted_at, queue, scheduled_at, state,
       CASE WHEN state = 'available'
            THEN pg_notify('oban_insert', '{"queue":"' || queue || '"}')
       END
FROM inserted;
