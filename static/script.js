// --- Element References ---
const stopSection = document.getElementById('stop-section');
const goSection = document.getElementById('go-section');
const stopText = document.getElementById('stop-text');
const goText = document.getElementById('go-text');

// --- Initial State ---
// A disconnected state is shown by default until the first WebSocket message is received.
function setDisconnectedState() {
    stopText.classList.add('hidden');
    goText.classList.add('hidden');
    stopSection.style.backgroundColor = '#343a40'; // Dark Gray
    goSection.style.backgroundColor = '#343a40'; // Dark Gray
}

setDisconnectedState();

// --- WebSocket Connection ---
// The client will automatically connect to the Socket.IO server that served the page.
const socket = io();

socket.on('connect', () => {
    console.log('Successfully connected to the server via WebSocket.');
});

socket.on('disconnect', () => {
    console.warn('Disconnected from the server.');
    setDisconnectedState();
});

socket.on('connect_error', (error) => {
    console.error('WebSocket connection error:', error);
    setDisconnectedState();
});

// --- Real-time Status Updates ---
socket.on("status_update", (data) => {
  console.log(`Received status update:`, data);
  const speed = data.speed;

  if (speed > 0) {
    // Vehicle is MOVING -> Show STOP
    stopText.classList.remove("hidden");
    goText.classList.add("hidden");

    stopSection.style.backgroundColor = "#FF0000"; // Red
    goSection.style.backgroundColor = "#6c757d"; // Gray

    stopSection.classList.add("large");
    stopSection.classList.remove("small");

    goSection.classList.add("small");
    goSection.classList.remove("large");
  } else {
    // Vehicle is STOPPED -> Show GO
    stopText.classList.add("hidden");
    goText.classList.remove("hidden");

    stopSection.style.backgroundColor = "#6c757d"; // Gray
    goSection.style.backgroundColor = "#66FF00"; // Green

    stopSection.classList.add("small");
    stopSection.classList.remove("large");

    goSection.classList.add("large");
    goSection.classList.remove("small");
  }
});
