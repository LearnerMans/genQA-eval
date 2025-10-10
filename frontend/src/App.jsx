import { useEffect, useState } from 'react'
import Projects from './pages/Projects'
import Project from './pages/Project'
import Test from './pages/Test'

function App() {
  const [route, setRoute] = useState(window.location.hash || '')

  useEffect(() => {
    const onHashChange = () => setRoute(window.location.hash || '')
    window.addEventListener('hashchange', onHashChange)
    return () => window.removeEventListener('hashchange', onHashChange)
  }, [])

  const testMatch = route.match(/^#project\/([^/]+)\/test\/([^/]+)$/)
  if (testMatch) {
    return <Test projectId={testMatch[1]} testId={testMatch[2]} />
  }
  const match = route.match(/^#project\/(.+)$/)
  if (match) {
    return <Project projectId={match[1]} />
  }
  return <Projects />
}

export default App
