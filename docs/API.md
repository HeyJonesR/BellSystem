# ChapelBells REST API Reference

## Overview

ChapelBells provides a RESTful HTTP API for managing schedules, audio, and system settings. The API is accessible at `http://localhost:5000/api/` and requires simple authentication.

## Authentication

**Bearer Token:**
```
Authorization: Bearer YOUR_TOKEN
```

Replace `YOUR_TOKEN` with the configured secret key (default: set in environment variable `CHAPEL_BELLS_SECRET`).

## Base URL

```
http://localhost:5000/api
```

## Endpoints

### System Status

#### Get System Status
```
GET /api/status
```

**Response:**
```json
{
  "running": true,
  "current_time": "2024-01-15T14:30:00",
  "sunrise": "2024-01-15T07:15:00",
  "sunset": "2024-01-15T17:45:00",
  "is_daytime": true,
  "quiet_hours_enabled": true,
  "quiet_hours": {
    "start": "21:00",
    "end": "07:00"
  },
  "audio_profiles": ["westminster", "carillon", "traditional"],
  "scheduled_events": 5
}
```

---

### Events Management

#### List All Events
```
GET /api/events
```

**Response:**
```json
[
  {
    "name": "Hourly Chimes",
    "rule": "every hour",
    "profile": "westminster",
    "tone": "bell",
    "active_after": "07:00",
    "active_before": "21:00",
    "description": "Traditional hourly chimes"
  },
  {
    "name": "Sunday Service",
    "rule": "sunday at 10:00",
    "profile": "carillon",
    "tone": "bell",
    "active_after": null,
    "active_before": null,
    "description": "Sunday worship service bell"
  }
]
```

#### Create Event
```
POST /api/events
Content-Type: application/json

{
  "name": "New Event",
  "rule": "sunday at 10:00",
  "profile": "carillon",
  "tone": "bell",
  "active_after": "07:00",
  "active_before": "21:00",
  "description": "New bell event"
}
```

**Response:** `201 Created`
```json
{
  "status": "success",
  "event": {
    "name": "New Event",
    "rule": "sunday at 10:00",
    "profile": "carillon",
    "tone": "bell",
    "active_after": "07:00",
    "active_before": "21:00",
    "description": "New bell event"
  }
}
```

#### Delete Event
```
DELETE /api/events/{event_name}
```

**Response:** `200 OK`
```json
{
  "status": "success"
}
```

---

### Quiet Hours

#### Get Quiet Hours
```
GET /api/quiet-hours
```

**Response:**
```json
{
  "enabled": true,
  "start": "21:00",
  "end": "07:00",
  "override_dates": ["2024-12-25", "2024-04-20"]
}
```

#### Update Quiet Hours
```
PUT /api/quiet-hours
Content-Type: application/json

{
  "enabled": true,
  "start": "22:00",
  "end": "08:00",
  "override_dates": ["2024-12-25"]
}
```

**Response:** `200 OK`
```json
{
  "status": "success",
  "data": {
    "enabled": true,
    "start": "22:00",
    "end": "08:00",
    "override_dates": ["2024-12-25"]
  }
}
```

---

### Audio Management

#### List Available Profiles
```
GET /api/audio/profiles
```

**Response:**
```json
[
  "westminster",
  "carillon",
  "traditional",
  "light",
  "custom"
]
```

#### Test Audio Playback
```
POST /api/audio/play
Content-Type: application/json

{
  "profile": "westminster",
  "tone": "bell"
}
```

**Response:** `200 OK`
```json
{
  "status": "success",
  "message": "Playing westminster/bell"
}
```

---

### History & Logs

#### Get Playback History
```
GET /api/history?limit=100
```

**Query Parameters:**
- `limit` (int, default: 100) - Maximum records to return

**Response:**
```json
[
  {
    "event": "Hourly Chimes",
    "time": "2024-01-15T14:00:00",
    "profile": "westminster",
    "tone": "bell"
  },
  {
    "event": "Hourly Chimes",
    "time": "2024-01-15T13:00:00",
    "profile": "westminster",
    "tone": "bell"
  }
]
```

---

### Settings

#### Get All Settings
```
GET /api/settings
```

**Response:**
```json
{
  "astro": {
    "latitude": 40.7128,
    "longitude": -74.0060
  },
  "audio": {
    "volume": 80,
    "backend": "alsa"
  }
}
```

#### Update Astronomical Settings
```
PUT /api/settings/astro
Content-Type: application/json

{
  "latitude": 42.3601,
  "longitude": -71.0589,
  "timezone_offset": -5
}
```

**Response:** `200 OK`
```json
{
  "status": "success"
}
```

#### Update Audio Settings
```
PUT /api/settings/audio
Content-Type: application/json

{
  "volume": 75,
  "backend": "pulse"
}
```

**Response:** `200 OK`
```json
{
  "status": "success"
}
```

---

### Configuration

#### Export Configuration
```
GET /api/export
```

**Response:** `200 OK` with JSON configuration
```json
{
  "quiet_hours": {
    "enabled": true,
    "start": "21:00",
    "end": "07:00",
    "override_dates": []
  },
  "events": [
    {
      "name": "Hourly Chimes",
      "rule": "every hour",
      "profile": "westminster",
      "tone": "bell"
    }
  ]
}
```

---

## Scheduling Rule Formats

### Natural Language

```
"every hour"              → Top of each hour (HH:00)
"sunday at 10:00"         → Every Sunday at 10:00 AM
"wednesday at 19:30"      → Every Wednesday at 7:30 PM
"first sunday at 08:00"   → First Sunday of month at 8 AM
```

### Cron Format

Standard Unix cron format: `minute hour day month weekday`

```
"0 12 * * *"              → Noon every day
"0 10 * * 1"              → 10 AM every Monday
"0 6 25 12 *"             → 6 AM on December 25 (Christmas)
"30 19 * * 3"             → 7:30 PM every Wednesday
"0 8 * * 0"               → 8 AM every Sunday
"*/30 * * * *"            → Every 30 minutes
```

---

## Error Responses

All errors return JSON with status code and error message:

```json
{
  "error": "Invalid rule format: xyz"
}
```

### Common Status Codes

- `200 OK` - Success
- `201 Created` - Resource created
- `400 Bad Request` - Invalid input
- `401 Unauthorized` - Authentication required
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

---

## Examples

### cURL

```bash
# Get system status
curl http://localhost:5000/api/status

# Create new event
curl -X POST http://localhost:5000/api/events \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sunday Service",
    "rule": "sunday at 10:00",
    "profile": "carillon"
  }'

# Update quiet hours
curl -X PUT http://localhost:5000/api/quiet-hours \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true,
    "start": "22:00",
    "end": "07:00"
  }'

# Test audio
curl -X POST http://localhost:5000/api/audio/play \
  -H "Content-Type: application/json" \
  -d '{"profile": "westminster"}'
```

### Python

```python
import requests

BASE_URL = "http://localhost:5000/api"

# Get status
response = requests.get(f"{BASE_URL}/status")
print(response.json())

# Create event
event = {
    "name": "New Bell",
    "rule": "sunday at 10:00",
    "profile": "carillon"
}
response = requests.post(f"{BASE_URL}/events", json=event)
print(response.json())

# Get history
response = requests.get(f"{BASE_URL}/history?limit=50")
for record in response.json():
    print(f"{record['time']}: {record['event']}")
```

### JavaScript

```javascript
const BASE_URL = "http://localhost:5000/api";

// Get status
fetch(`${BASE_URL}/status`)
  .then(r => r.json())
  .then(data => console.log(data));

// Create event
fetch(`${BASE_URL}/events`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    name: "New Bell",
    rule: "sunday at 10:00",
    profile: "carillon"
  })
})
  .then(r => r.json())
  .then(data => console.log(data));

// Test audio
fetch(`${BASE_URL}/audio/play`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    profile: "westminster",
    tone: "bell"
  })
})
  .then(r => r.json())
  .then(data => console.log(data));
```

---

## Rate Limiting

No explicit rate limiting is implemented. For production deployment, consider adding:
- Rate limit middleware (Flask-Limiter)
- Request throttling on high-frequency endpoints
- API key rotation for authentication

---

## Webhooks (Future)

Future versions may support webhook callbacks for:
- Bell triggered events
- Service status changes
- Error notifications
- Configuration changes

---

## SDK/Client Libraries

(To be developed)

- Python client library
- JavaScript/Node.js client
- cURL examples (provided above)

---

For more information, see [README.md](../README.md)
