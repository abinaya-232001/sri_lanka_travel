import { useOutletContext } from 'react-router-dom'
import ChatBox from '../components/ChatBox'
import FamilyAlertStatus from '../components/FamilyAlertStatus'
import GuidanceCard from '../components/GuidanceCard'
import ActivityStatus from '../components/ActivityStatus'
import SosBar from '../components/SosBar'

export default function TouristDashboard() {
  const { me, incident, setIncident, sendSos, sending, sosError } = useOutletContext()

  return (
    <>
      <section className="sos-hero">
        <header className="page-head">
          <h1>{me?.name || 'Emergency assistance'}</h1>
          <p>Describe what is happening. Your location goes to the nearest police station.</p>
        </header>
        <SosBar language={me?.language || 'en'} sending={sending} hasOpenCase={Boolean(incident)} onSend={sendSos} />
      </section>
      {sosError && <div className="alert alert-danger" role="alert">{sosError}</div>}

      {incident ? (
        <>
          <ActivityStatus status={incident.status} />
          <GuidanceCard guidance={incident.guidance} status={incident.status} />
          <FamilyAlertStatus alerts={incident.family_alerts} onUpdate={(family_alerts) => setIncident((prev) => ({ ...prev, family_alerts }))} />
          <ChatBox
            role="tourist"
            incidentId={incident.id}
            title={incident.station?.name || 'Nearest police station'}
            subtitle="Officers can see your messages, photos and voice notes"
            language={me?.language || 'en'}
            onIncident={(inc) => setIncident((prev) => ({ ...inc, family_alerts: prev?.family_alerts }))}
          />
        </>
      ) : (
        <section className="card">
          <h2>How SOS works</h2>
          <ol className="steps">
            <li><span className="step-n">1</span><span>Describe what is happening, or record a voice note, then send SOS.</span></li>
            <li><span className="step-n">2</span><span>You receive a safety tip and the numbers to call for this situation.</span></li>
            <li><span className="step-n">3</span><span>The nearest station receives your message and live location, and can reply in chat.</span></li>
            <li><span className="step-n">4</span><span>On your safety card, press Send. That family number receives your message and your current location.</span></li>
          </ol>
          <div className="hotlines">
            <a className="hotline" href="tel:119"><span>Police</span><b>119</b></a>
            <a className="hotline" href="tel:1990"><span>Ambulance</span><b>1990</b></a>
          </div>
        </section>
      )}
    </>
  )
}
