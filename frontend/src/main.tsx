import React from 'react'
import ReactDOM from 'react-dom/client'
import './index.css' // <-- BẮT BUỘC PHẢI CÓ DÒNG NÀY ĐỂ TRÌNH DUYỆT NHẬN CSS
import App from './App'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)