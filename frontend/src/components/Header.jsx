import { AppBar, Toolbar, Typography, Button, Box } from '@mui/material'
import { useNavigate } from 'react-router-dom'

const Header = () => {
  const navigate = useNavigate()
  
  return (
    <AppBar position="fixed">
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          IntelliX.AI Test Case Generator
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button color="inherit" onClick={() => navigate('/')}>Generate</Button>
          <Button color="inherit" onClick={() => navigate('/search')}>Search</Button>
        </Box>
      </Toolbar>
    </AppBar>
  )
}

export default Header
