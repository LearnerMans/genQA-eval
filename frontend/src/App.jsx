import { useEffect, useState } from 'react'
import Projects from './pages/Projects'
import Project from './pages/Project'
import Test from './pages/Test'
import EvalResult from './pages/EvalResult'
import ThemeSwitcher from './components/ThemeSwitcher'

function App() {
  const [route, setRoute] = useState(window.location.hash || '')

  useEffect(() => {
    const onHashChange = () => setRoute(window.location.hash || '')
    window.addEventListener('hashchange', onHashChange)
    return () => window.removeEventListener('hashchange', onHashChange)
  }, [])

  const testMatch = route.match(/^#project\/([^/]+)\/test\/([^/]+)$/)
  if (testMatch) {
    return (
      <>
        <Test projectId={testMatch[1]} testId={testMatch[2]} />
        <ThemeSwitcher />
      </>
    )
  }
  const evalMatch = route.match(/^#project\/([^/]+)\/test\/([^/]+)\/run\/([^/]+)\/qa\/([^/]+)$/)
  if (evalMatch) {
    return (
      <>
        <EvalResult
          projectId={evalMatch[1]}
          testId={evalMatch[2]}
          runId={evalMatch[3]}
          qaId={evalMatch[4]}
        />
        <ThemeSwitcher />
      </>
    )
  }
  const match = route.match(/^#project\/(.+)$/)
  if (match) {
    return (
      <>
        <Project projectId={match[1]} />
        <ThemeSwitcher />
      </>
    )
  }
  return (
    <>
      <Projects />
      <ThemeSwitcher />
    </>
  )
}

export default App
