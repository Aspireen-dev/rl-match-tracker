import { useEffect, useState } from 'react'

// Forme de la réponse de GET /api/health : le contrat, typé à la frontière.
type HealthStatus = {
  status: string
}

function App() {
  // useState : la valeur survit aux re-rendus du composant.
  const [status, setStatus] = useState('')

  useEffect(() => {
    fetch('/api/health')
      .then((response) => {
        // fetch ne rejette QUE sur une erreur réseau : les 404/500 passent ici.
        if (!response.ok) {
          throw new Error(`Health check failed with HTTP ${response.status}`)
        }
        return response.json()
      })
      // Le corps arrive en texte : json() le déserialise (et renvoie any, d'où le type sur le paramètre).
      .then((data: HealthStatus) => setStatus(data.status))
      .catch((error) => {
        // Point unique d'erreur : réseau ET HTTP (le throw ci-dessus atterrit ici).
        console.error('Error fetching health status:', error)
        setStatus('Error')
      })
  }, []) // Dépendances vides : l'effet ne joue qu'une fois, au montage du composant.

  return (
    <main>
      <h1>RL Match Tracker</h1>
      <h2>Health Status: {status}</h2>
    </main>
  )
}

export default App
