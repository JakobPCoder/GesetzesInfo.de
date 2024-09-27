// src/App.js
import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import MainPage from './pMainPage';
import AboutPage from './pAboutPage';
import AdSenseScript from './components/ads/adsense';
import './App.css'; // This ensures your CSS for App is still applied
import './sMainPage.css'; // This ensures your CSS for App is still applied

const App = () => (
  <Router>
    <AdSenseScript />
    <Routes>
      <Route path="/" element={<MainPage />} />
      <Route path="/about" element={<AboutPage />} />
    </Routes>
  </Router>
);

export default App;