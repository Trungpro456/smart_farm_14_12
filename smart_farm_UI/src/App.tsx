import { Provider } from 'react-redux'
import './App.css'
import AppRouter from './routes/index.route'
import { store } from './stores'

function App() {
  return (
    <Provider store={store}>
      <AppRouter />
    </Provider>
  )
}

export default App
