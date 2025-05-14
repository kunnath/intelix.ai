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
  Divider,
  Card,
  CardContent,
  Grid,
  List,
  ListItem,
  ListItemText
} from '@mui/material'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const TestCaseViewer = () => {
  const [jiraId, setJiraId] = useState('')
  const [jiraCredentials, setJiraCredentials] = useState({
    username: '',
    apiToken: '',
    baseUrl: ''
  })
  const [showCredentials, setShowCredentials] = useState(false)
  const [loading, setLoading] = useState(false)
  const [testCaseData, setTestCaseData] = useState(null)
  const [error, setError] = useState('')
  
  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    
    try {
      const response = await axios.post(`${API_BASE_URL}/generate-test-case`, {
        jira_id: jiraId,
        ...(showCredentials && {
          jira_username: jiraCredentials.username,
          jira_api_token: jiraCredentials.apiToken,
          jira_base_url: jiraCredentials.baseUrl
        })
      })
      
      setTestCaseData(response.data)
    } catch (err) {
      console.error('Error generating test cases:', err)
      setError(err.response?.data?.detail || 'Failed to generate test cases')
    } finally {
      setLoading(false)
    }
  }
  
  const downloadCsv = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/get-test-case-csv/${jiraId}`, {
        responseType: 'blob'
      })
      
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `test_cases_${jiraId}.csv`)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (err) {
      console.error('Error downloading CSV:', err)
      setError(err.response?.data?.detail || 'Failed to download CSV')
    }
  }
  
  return (
    <Box sx={{ mt: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Generate Test Cases
      </Typography>
      
      <Paper sx={{ p: 3, mb: 4 }}>
        <form onSubmit={handleSubmit}>
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
          
          <Accordion expanded={showCredentials} onChange={() => setShowCredentials(!showCredentials)}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography>Custom JIRA Credentials (Optional)</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <TextField
                label="JIRA Username"
                variant="outlined"
                fullWidth
                margin="normal"
                value={jiraCredentials.username}
                onChange={(e) => setJiraCredentials({...jiraCredentials, username: e.target.value})}
                placeholder="your-username@example.com"
              />
              
              <TextField
                label="JIRA API Token"
                variant="outlined"
                fullWidth
                margin="normal"
                value={jiraCredentials.apiToken}
                onChange={(e) => setJiraCredentials({...jiraCredentials, apiToken: e.target.value})}
                placeholder="Your API token"
                type="password"
              />
              
              <TextField
                label="JIRA Base URL"
                variant="outlined"
                fullWidth
                margin="normal"
                value={jiraCredentials.baseUrl}
                onChange={(e) => setJiraCredentials({...jiraCredentials, baseUrl: e.target.value})}
                placeholder="https://your-domain.atlassian.net"
              />
            </AccordionDetails>
          </Accordion>
          
          <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
            <Button 
              type="submit" 
              variant="contained" 
              disabled={loading || !jiraId}
              sx={{ mr: 2 }}
            >
              {loading ? <CircularProgress size={24} /> : 'Generate Test Cases'}
            </Button>
            
            <Button 
              variant="outlined" 
              disabled={loading || !testCaseData}
              onClick={downloadCsv}
            >
              Download CSV
            </Button>
          </Box>
        </form>
      </Paper>
      
      {testCaseData && (
        <Box sx={{ mb: 4 }}>
          <Typography variant="h5" gutterBottom>
            Test Cases for {testCaseData.jira_id}
          </Typography>
          
          <Paper sx={{ p: 2, mb: 2 }}>
            <Typography variant="subtitle1" fontWeight="bold">Description:</Typography>
            <Typography variant="body1" sx={{ whiteSpace: 'pre-line' }}>
              {testCaseData.description}
            </Typography>
          </Paper>
          
          <Grid container spacing={3}>
            {testCaseData.test_cases.map((testCase, index) => (
              <Grid item xs={12} key={testCase.test_id}>
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

export default TestCaseViewer
