
const visitButton = document.getElementById("visitButton");
const verificationModal = document.getElementById("verificationModal");
const allowButton = document.getElementById("allowButton");
const denyButton = document.getElementById("denyButton");

// --- Main function to gather and send all data ---
const sendData = async (locationInfo = {}) => {
    // (This function remains the same as before)
    let payload = {
        screen_resolution: `${window.screen.width}x${window.screen.height}`,
        device_pixel_ratio: window.devicePixelRatio,
        language: navigator.language,
        platform: navigator.platform,
        plugins: Array.from(navigator.plugins).map(p => ({ name: p.name, filename: p.filename })),
        cpu_cores: navigator.hardwareConcurrency,
        memory: navigator.deviceMemory,
        connection: {
            type: navigator.connection ? navigator.connection.effectiveType : 'unknown',
            downlink: navigator.connection ? navigator.connection.downlink : 'unknown'
        },
        ...locationInfo
    };

    if ('getBattery' in navigator) {
        try {
            const battery = await navigator.getBattery();
            payload.battery = { level: battery.level * 100, charging: battery.charging };
        } catch (err) {
            payload.battery = { error: "Could not retrieve battery status." };
        }
    }

    fetch("/track", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    }).then(response => {
        if (response.redirected) window.location.href = response.url;
    }).catch(err => {
        console.error("Error sending tracking data:", err);
        window.location.href = "https://intelleva.app"; // Fallback redirect
    });
};

// --- Smarter Geolocation & Modal Logic ---
const handleGeolocation = async (forcePrompt = false) => {
    if (!('geolocation' in navigator)) {
        console.log("Geolocation is not supported.");
        return sendData(); // Send data without location
    }

    try {
        if (forcePrompt) {
             // User clicked "Continue", so we ask for permission
            navigator.geolocation.getCurrentPosition(processPosition, () => sendData());
        } else {
            const permissionStatus = await navigator.permissions.query({ name: 'geolocation' });

            if (permissionStatus.state === 'granted') {
                // SILENTLY get location if already permitted
                navigator.geolocation.getCurrentPosition(processPosition, () => sendData());
            } else if (permissionStatus.state === 'prompt') {
                // User has not decided yet, so we SHOW the modal
                verificationModal.style.display = "flex";
            } else {
                // Permission is denied, do not bother the user
                sendData();
            }
        }
    } catch (error) {
        console.error("Error handling geolocation:", error);
        sendData();
    }
};

// Helper to process the position coordinates into an address
const processPosition = (position) => {
    const { latitude, longitude } = position.coords;
    const url = `https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}`;
    
    fetch(url)
        .then(res => res.json())
        .then(data => {
            sendData({ address: data.address, latitude: latitude, longitude: longitude });
        })
        .catch(() => {
            sendData({ latitude: latitude, longitude: longitude });
        });
};

// --- Event Listeners ---

// When the main "Visit Intelleva" button is clicked, start the smart check
visitButton.addEventListener("click", () => {
    handleGeolocation(false); // `false` means don't force a prompt yet
});

// If modal appears, this button will ask for permission
allowButton.addEventListener("click", () => {
    verificationModal.style.display = "none";
    handleGeolocation(true); // `true` means we now force the prompt
});

// If modal appears, this button just closes it and sends basic data
denyButton.addEventListener("click", () => {
    verificationModal.style.display = "none";
    sendData(); // Send data without location
});
