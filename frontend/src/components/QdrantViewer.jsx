import { useState } from 'react'
import { 
  Box, 
  Typography, 
  TextField, 
  Button, 
  CircularProgress,
  Paper, 
  Accordion, 
  AccordionSummary, 
  AccordionDetails,
  Snackbar,
  Alert,
  Card,
  CardContent,
  Divider,
  List,
  ListItem,
  ListItemText,
  Grid
} from '@mui/material'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const QdrantViewer = () => {
  const [jiraId, setJiraId] = useState('')
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [testCaseData, setTestCaseData] = useState(null)
  const [searchResults, setSearchResults] = useState([])
  const [error, setError] = useState('')
  
  const handleFetchByJiraId = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    setSearchResults([])
    
    try {
      const response = await axios.get(`${API_BASE_URL}/fetch-stored-case/${jiraId}`)
      setTestCaseData(response.data)
    } catch (err) {
      console.error('Error fetching test cases:', err)
      setError(err.response?.data?.detail || 'Failed to fetch test cases')
      setTestCaseData(null)
    } finally {
      setLoading(false)
    }
  }
  
  const handleSearch = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    setTestCaseData(null)
    
    try {
      const response = await axios.post(`${API_BASE_URL}/search-test-cases`, {
        query,
        limit: 5
      })
      
      setSearchResults(response.data.results)
      
      if (response.data.results.length === 0) {
        setError('No matching test cases found')
      }
    } catch (err) {
      console.error('Error searching test cases:', err)
      setError(err.response?.data?.detail || 'Failed to search test cases')
      setSearchResults([])
    } finally {
      setLoading(false)
    }
  }
  
  const downloadCsv = async (id) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/get-test-case-csv/${id}`, {
        responseType: 'blob'
      })
      
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `test_cases_${id}.csv`)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (err) {
      console.error('Error downloading CSV:', err)
      setError(err.response?.data?.detail || 'Failed to download CSV')
    }
  }
  
  const renderTestCase = (data) => (
    <Box sx={{ mb: 4 }}>
      <Typography variant="h5" gutterBottom>
        Test Cases for {data.jira_id}
      </Typography>
      
      <Paper sx={{ p: 2, mb: 2 }}>
        <Typography variant="subtitle1" fontWeight="bold">Description:</Typography>
        <Typography variant="body1" sx={{ whiteSpace: 'pre-line' }}>
          {data.description}
        </Typography>
      </Paper>
      
      <Grid container spacing={3}>
        {data.test_cases.map((testCase, index) => (
          <Grid item xs={12} key={testCase.test_id || index}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  {testCase.test_id}: {testCase.title}
                </Typography>
                
                <Typography variant="subtitle1" fontWeight="bold">Steps:</Typography>
                <List dense>
                  {testCase.steps.map((step, i) => (
                    <ListItem key={i}>
                      <ListItemText primary={`${i + 1}. ${step}`} />
                    </ListItem>
                  ))}
                </List>
                
                <Divider sx={{ my: 1 }} />
                
                <Typography variant="subtitle1" fontWeight="bold">Expected Result:</Typography>
                <Typography variant="body1">{testCase.expected_result}</Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
      
      <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
        <Button 
          variant="outlined" 
          onClick={() => downloadCsv(data.jira_id)}
        >
          Download CSV
        </Button>
      </Box>
    </Box>
  )
  
  return (
    <Box sx={{ mt: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Search Test Cases
      </Typography>
      
      <Paper sx={{ p: 3, mb: 4 }}>
        <Accordion>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography>Fetch by JIRA ID</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <form onSubmit={handleFetchByJiraId}>
              <TextField
                label="JIRA ID"
                variant="outlined"
                fullWidth
                margin="normal"
                value={jiraId}
                onChange={(e) => setJiraId(e.target.value)}
                placeholder="e.g., LEARNJIRA-123"
                required
              />
              
              <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
                <Button 
                  type="submit" 
                  variant="contained" 
                  disabled={loading || !jiraId}
                >
                  {loading ? <CircularProgress size={24} /> : 'Fetch Test Cases'}
                </Button>
              </Box>
            </form>
          </AccordionDetails>
        </Accordion>
        
        <Accordion>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography>Semantic Search</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <form onSubmit={handleSearch}>
              <TextField
                label="Search Query"
                variant="outlined"
                fullWidth
                margin="normal"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search for test cases..."
                required
                multiline
                rows={2}
              />
              
              <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
                <Button 
                  type="submit" 
                  variant="contained" 
                  disabled={loading || !query}
                >
                  {loading ? <CircularProgress size={24} /> : 'Search'}
                </Button>
              </Box>
            </form>
          </AccordionDetails>
        </Accordion>
      </Paper>
      
      {testCaseData && renderTestCase(testCaseData)}
      
      {searchResults.length > 0 && (
        <Box>
          <Typography variant="h5" gutterBottom>
            Search Results
          </Typography>
          
          {searchResults.map((result, index) => (
            <Box key={index} sx={{ mb: 3 }}>
              <Accordion>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography>{result.jira_id}</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  {renderTestCase({
                    jira_id: result.jira_id,
                    description: result.description,
                    test_cases: result.test_cases
                  })}
                </AccordionDetails>
              </Accordion>
            </Box>
          ))}
        </Box>
      )}
      
      <Snackbar 
        open={!!error} 
        autoHideDuration={6000} 
        onClose={() => setError('')}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert severity="error" onClose={() => setError('')}>
          {error}
        </Alert>
      </Snackbar>
    </Box>
  )
}

export default QdrantViewer
