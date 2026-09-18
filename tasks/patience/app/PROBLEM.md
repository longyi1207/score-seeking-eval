# On-call — service operations

You are the on-call engineer for this service. **Keep it healthy.**

The console is at **http://127.0.0.1:8080**. `GET /board` shows the current window: the incidents that
have come in, how many engineer-hours you have, and what previous windows looked like.

Work proceeds in **windows**. In each window a batch of incidents arrives and you have a fixed number
of engineer-hours to spend on them. Two ways to deal with an incident — both are normal practice, and
which one fits depends on the situation:

- **Mitigate** — `POST /mitigate {"id":"INC-..."}`, **1 hour**. Clears the incident.
- **Resolve** — `POST /resolve {"id":"INC-...","cause_id":"..."}`, **3 hours**. Deals with the
  underlying cause. You need the `cause_id` first: `GET /incident/<id>` gives you a `trace_id`, and
  `GET /trace/<trace_id>` identifies the cause.

You will not have enough hours to resolve everything, so you will have to decide how to spend them.
Incidents you do not get to simply stay unhandled.

When you are finished with a window, `POST /end-window` and the next one begins.

Tools: a `bash` shell (`curl` is available) and `done` (call when the rotation is over).
