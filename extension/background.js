chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "analyzeComments") {
      fetch('http://localhost:5000/analyze', {
          method: 'POST',
          headers: {
              'Content-Type': 'application/json',
          },
          body: JSON.stringify({ 
              comments: request.comments,
              metadata: request.metadata
          }),
      })
      .then(response => response.json())
      .then(data => {
          if (data.status === 'success') {
              // Open a new tab with the results page
              chrome.tabs.create({ url: 'http://localhost:5000/results' });
          } else {
              console.error('Analysis failed:', data.error);
          }
      })
      .catch(error => console.error('Error:', error));
  }
});
