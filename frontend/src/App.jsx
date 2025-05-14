import { useState } from 'react'
import { Routes, Route } from 'react-router-dom'
import { Box, Container } from '@mui/material'
import Header from './components/Header'
import TestCaseViewer from './components/TestCaseViewer'
import QdrantViewer from './components/QdrantViewer'

function App() {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <Header />
      <Container component="main" sx={{ mt: 8, mb: 2, flex: 1 }}>
        <Routes>
          <Route path="/" element={<TestCaseViewer />} />
          <Route path="/search" element={<QdrantViewer />} />
        </Routes>
      </Container>
      <Box component="footer" sx={{ py: 3, px: 2, mt: 'auto', backgroundColor: (theme) => theme.palette.grey[200] }}>
        <Container maxWidth="sm">
          <Box textAlign="center">
            IntelliX.AI © {new Date().getFullYear()}
          </Box>
        </Container>
      </Box>
    </Box>
  )
}

export default App
