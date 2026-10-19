const STEPS = ['Alert received', 'Police notified', 'Unit dispatched', 'Unit arrived']

function reachedFor(status) {
  if (status === 'acknowledged') return 2
  if (status === 'responding') return 3
  if (status === 'resolved' || status === 'closed') return 4
  return 1
}

export default function ActivityStatus({ status }) {
  const reached = reachedFor(status)
  const finished = reached === 4
  return (
    <ol className="activity" aria-label="Activity status">
      {STEPS.map((label, i) => {
        const state = finished || i < reached - 1 ? 'done' : i === reached - 1 ? 'now' : 'wait'
        return (
          <li key={label} className="step-wrap" style={{ display: 'contents' }}>
            <div className={`step ${state}`} aria-current={state === 'now' ? 'step' : undefined}>
              <span className="n">{i + 1}</span>
              <span className="lbl">{label}</span>
            </div>
            {i < STEPS.length - 1 && <span className={`join${i < reached - 1 || finished ? ' on' : ''}`} aria-hidden="true" />}
          </li>
        )
      })}
    </ol>
  )
}
