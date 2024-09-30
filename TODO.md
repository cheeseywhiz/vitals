# vitals

## TODO

- if the need arises, use celery to manage sync tasks.
  * discogs will institute a 30-60 second rate limiter. this could break browser timeouts. this is why we need async tasks. normal wsgi apps aren't meant for long running task management which is why we need a task manager (celery).
  * then use websockets so that we don't have to poll for the task state.
