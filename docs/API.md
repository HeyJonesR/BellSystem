# REST API Reference

Base URL: `http://<host>:5000`

No authentication required (designed for local network use).

---

## System Status

### GET /api/status

```json
{
  "scheduled_bells": 3,
  "quiet_hours_enabled": true,
  "quiet_hours": { "start": "22:00", "end": "07:00" },
  "is_quiet_now": false,
  "current_time": "14:30:00"
}
```

---

## Schedule (Bells)

### GET /api/schedule

Returns the bells array from config.

```json
[
  {
    "time": "09:00",
    "sound": "carillon-bells/westminster-chimes-full.mp3"
  },
  {
    "time": "12:00",
    "sound": "carillon-bells/noon-hour-bell-strike.mp3",
    "count": 1,
    "interval": 2.0
  }
]
```

### POST /api/schedule

Add a new bell.

```json
{
  "time": "10:00",
  "sound": "carillon-bells/joyful-joyful.mp3",
  "count": 3,
  "interval": 2.0
}
```

**Fields:**
- `time` (required) — `HH:MM` format
- `sound` (required) — relative path inside `audio_samples/`
- `count` (optional) — number of rings, default 1
- `interval` (optional) — seconds between rings, minimum 0.5

Response: `201` with `{ "status": "ok", "bells": [...] }`

### PUT /api/schedule/:idx

Update bell at index `idx` (0-based). Same body as POST.

### DELETE /api/schedule/:idx

Delete bell at index `idx`.

---

## Sounds

### GET /api/sounds

List all available sound files.

```json
[
  { "path": "carillon-bells/america-the-beautiful.mp3", "label": "America The Beautiful" },
  { "path": "carillon-bells/ave-maria.mp3", "label": "Ave Maria" },
  { "path": "westminster/bell.wav", "label": "Westminster – Bell" }
]
```

---

## Playback

### POST /api/trigger

Play a sound manually.

```json
{ "sound": "carillon-bells/westminster-chimes-full.mp3" }
```

Response: `{ "status": "ok" }`

Plays in a background thread. Respects quiet hours.

### POST /api/stop

Stop all currently playing sounds.

---

## Volume

### PUT /api/volume

```json
{ "volume": 80 }
```

Response: `{ "volume": 80 }`

Range: 0–100.

---

## Quiet Hours

### PUT /api/quiet_hours

```json
{
  "enabled": true,
  "start": "22:00",
  "end": "07:00"
}
```

Response: same as GET /api/status.

---

## History

### GET /api/history

Query param: `?limit=50` (default 50, max 200)

```json
[
  {
    "time": "2026-04-01 12:00:00",
    "sound": "carillon-bells/noon-hour-bell-strike.mp3",
    "count": 1
  }
]
```

History is in-memory (cleared on service restart).

---

## Error Responses

All errors return JSON:

```json
{ "error": "description of the problem" }
```

Common status codes: `400` (bad input), `404` (bell index not found).
