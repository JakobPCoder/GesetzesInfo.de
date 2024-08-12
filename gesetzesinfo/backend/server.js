const express = require('express');
const cors = require('cors'); 
const app = express();
const PORT = process.env.PORT || 3001;

app.use(cors()); // Enable CORS for all routes


app.get('/', (req, res) => {
  const q = req.query.q;
  res.send(q ? q.toString() : 'Hello from the Node.js backend!');
});

const dummySearchResults = [
  { id: 1, title: 'StGB § 212 Mord', text: '1. Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, sed diam voluptua. At vero eos et accusam et justo duo dolores et ea rebum. Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum dolor sit amet. Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, sed diam voluptua. At vero eos et accusam et justo duo dolores et ea rebum. Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum dolor sit amet.'},
  { id: 2, title: 'StGB § 213 Totschlag', text: '2. Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, sed diam voluptua. At vero eos et accusam et justo duo dolores et ea rebum. Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum dolor sit amet. Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, sed diam voluptua. At vero eos et accusam et justo duo dolores et ea rebum. Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum dolor sit amet.'},
  { id: 3, title: 'StGB § 214 Diebstahl', text: '3. Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, sed diam voluptua. At vero eos et accusam et justo duo dolores et ea rebum. Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum dolor sit amet. Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, sed diam voluptua. At vero eos et accusam et justo duo dolores et ea rebum. Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum dolor sit amet.'},
];

app.get('/api/search', (req, res) => {
  // Extract 'q' parameter from the query string
  const query = req.query.q;

  // Check if 'q' parameter is provided
  if (!query) {
    // If no 'q' parameter is provided, exit early and do nothing
    return res.status(400).json({ error: 'Query parameter q is required' });
  }

  // For now, return the dummy search results
  res.json(dummySearchResults);
});




app.listen(PORT, () => {  // Use PORT here, not port
  console.log(`Backend server is running at http://localhost:${PORT}`);
});
