# Web UI Wireframe & Component Design

## Dashboard Layout

```
┌────────────────────────────────────────────────────────────────┐
│                  CHAPELBELLS ADMINISTRATION                    │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  Status:  ✓ Running    Time: 2:30 PM    Sun/Set: 7:00/5:30   │
│  Quiet:   21:00-07:00  Events: 5        Audio: westminster   │
│                                                                │
├────────────────────────────────────────────────────────────────┤
│                       SCHEDULED EVENTS                         │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  🔔 Hourly Chimes          (every hour, 07:00-21:00)         │
│     Profile: westminster   Tone: bell                         │
│     Last ring: 2:00 PM     Next: 3:00 PM      [Edit] [Delete] │
│                                                                │
│  🔔 Sunday Service         (sunday at 10:00)                 │
│     Profile: carillon      Tone: bell                         │
│     Next: Jan 21, 10:00 AM                  [Edit] [Delete]  │
│                                                                │
│  🔔 Noon Chime             (every day at 12:00)              │
│     Profile: light         Tone: bell                         │
│     Last ring: 12:00 PM    Next: Tomorrow 12:00 PM [Edit]... │
│                                                                │
│  [+ Add New Event]                                             │
│                                                                │
├────────────────────────────────────────────────────────────────┤
│                       RECENT PLAYBACK                          │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  2024-01-15 14:00  Hourly Chimes     [westminster/bell]      │
│  2024-01-15 13:00  Hourly Chimes     [westminster/bell]      │
│  2024-01-15 12:00  Noon Chime        [light/bell]            │
│  2024-01-15 10:00  Hourly Chimes     [westminster/bell]      │
│                                                                │
│  [Show More] [Clear History]                                   │
│                                                                │
├────────────────────────────────────────────────────────────────┤
│  ⚙️ Settings  |  🔊 Audio  |  📅 Calendar  |  ? Help          │
└────────────────────────────────────────────────────────────────┘
```

## Settings Modal

```
┌────────────────────────────────────────────────────┐
│          SETTINGS                            [✕]  │
├────────────────────────────────────────────────────┤
│                                                   │
│  📍 Location                                      │
│  ├─ Latitude: [40.7128        ]                  │
│  ├─ Longitude: [-74.0060       ]                 │
│  └─ Timezone: [America/New_York  ▼]              │
│                                                   │
│  🕐 Quiet Hours                                   │
│  ├─ Enabled: [✓]                                │
│  ├─ Start Time: [21:00 ]                        │
│  ├─ End Time:   [07:00 ]                        │
│  └─ Override Dates:                              │
│     ├─ [X] 2024-12-25 (Christmas)              │
│     ├─ [+ Add Override Date]                    │
│                                                   │
│  🔊 Audio Settings                               │
│  ├─ Device: [default        ▼]                  │
│  ├─ Backend: [ALSA ▼]                           │
│  ├─ Volume: [████████░░] 80%                    │
│  │  [-] [  50%  ] [  100%  ] [+]                │
│  └─ Profile: [westminster ▼]                    │
│                                                   │
│  [Cancel]  [Save Changes]                        │
└────────────────────────────────────────────────────┘
```

## Add/Edit Event Modal

```
┌────────────────────────────────────────────────────┐
│          ADD NEW BELL EVENT                  [✕]  │
├────────────────────────────────────────────────────┤
│                                                   │
│  Event Name: [Sunday Service          ]        │
│                                                   │
│  Schedule Rule:                                   │
│  ○ Every Hour                                     │
│  ○ Specific Day & Time:  [Sunday ▼] [10:00]    │
│  ◉ Cron Format: [0 10 * * 0        ]           │
│                                                   │
│  Audio Configuration:                             │
│  ├─ Profile: [carillon ▼]                        │
│  ├─ Tone: [bell ▼]                               │
│  └─ [Test Audio]                                 │
│                                                   │
│  Active Hours (Optional):                         │
│  ├─ After:  [07:00 ]  ○ No limit                │
│  └─ Before: [21:00 ]  ○ No limit                │
│                                                   │
│  Description: [Sunday worship service bell  ]   │
│                                                   │
│  [Cancel]  [Save Event]                          │
└────────────────────────────────────────────────────┘
```

## Audio Test Panel

```
┌────────────────────────────────────────────────────┐
│          AUDIO PLAYBACK TEST                 [✕]  │
├────────────────────────────────────────────────────┤
│                                                   │
│  📦 Select Profile:                               │
│  ○ westminster (Westminster Quarters)           │
│  ○ carillon (Full Carillon)                     │
│  ○ traditional (Large Single Bell)              │
│  ○ light (Soft Chimes)                          │
│  ◉ custom (User Profile)                        │
│                                                   │
│  🎵 Select Tone:                                  │
│  [bell     ▼]                                     │
│                                                   │
│  🔊 Volume: [████████░░] 80%                    │
│     [  -  ]  [  50%  ]  [  100%  ]  [  +  ]     │
│                                                   │
│  [▶ Play] [⏹ Stop]  [Repeat 3x]                 │
│                                                   │
│  Status: Ready                                    │
│  Duration: 2.5s                                   │
│  Last Played: 2024-01-15 14:00:32                │
│                                                   │
└────────────────────────────────────────────────────┘
```

## Calendar View (Future)

```
┌─────────────────────────────────────────────────────────────┐
│                      CALENDAR VIEW                      [✕] │
├─────────────────────────────────────────────────────────────┤
│  January 2024                                               │
│  Sun   Mon   Tue   Wed   Thu   Fri   Sat                    │
│   31    1     2     3     4     5     6                     │
│    7    8     9    10    11    12    13                     │
│   14   15    16    17    18    19    20                     │
│   21   22    23    24    25    26    27                     │
│   28   29    30    31                                       │
│                                                             │
│  🔔 Hourly Chimes   (Every Hour, 7 AM - 9 PM)             │
│  🔔 Sunday Service  (Sunday 10 AM)                         │
│  🟡 Noon Chime      (Daily 12 PM)                          │
│                                                             │
│  Day View: January 15, 2024                                │
│  ├─ 07:00 Hourly Chimes (westminster)                     │
│  ├─ 08:00 Hourly Chimes (westminster)                     │
│  ├─ 09:00 Hourly Chimes (westminster)                     │
│  ├─ 10:00 Hourly Chimes (westminster)                     │
│  ├─ 12:00 Noon Chime (light)                              │
│  └─ [+ Add Special Event]                                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Mobile Responsive Design

```
Phone (Portrait):

┌─────────────────┐
│  CHAPELBELLS    │
├─────────────────┤
│ Status          │
│ Running ✓ 2:30P │
│ Quiet: 21-07    │
├─────────────────┤
│ EVENTS (5)      │
│ ─────────────── │
│ 🔔 Hourly       │
│    Next: 3 PM   │
│    [Edit]       │
│ ─────────────── │
│ 🔔 Sunday Svc   │
│    Next: Jan 21 │
│    [Edit]       │
│ ─────────────── │
│ [+ Add Event]   │
├─────────────────┤
│ RECENT (3)      │
│ ─────────────── │
│ 14:00 Hourly    │
│ 13:00 Hourly    │
│ 12:00 Noon      │
├─────────────────┤
│ ⚙️ ⚡ 📅 ?      │
└─────────────────┘
```

## Component Colors & Styling

```
Color Scheme:
├─ Primary: #007BFF (Blue)
├─ Success: #28A745 (Green)
├─ Warning: #FFC107 (Yellow)
├─ Danger: #DC3545 (Red)
├─ Background: #F8F9FA (Light Gray)
└─ Text: #333333 (Dark Gray)

Typography:
├─ Headers: Bold, 18-24px
├─ Labels: Medium, 12px
├─ Values: Regular, 14-16px
└─ Buttons: Medium, 14px

Spacing:
├─ Sections: 20px
├─ Elements: 15px
└─ Padding: 10-20px
```

## Interaction Patterns

### Adding Event
1. Click "[+ Add New Event]" button
2. Modal opens with form
3. Fill: Name, Rule, Profile, Tone
4. (Optional) Set active hours
5. Click "[Test Audio]" to preview
6. Click "[Save Event]"
7. Event appears in list
8. Next ring shown in status

### Editing Event
1. Click "[Edit]" button on event
2. Modal opens with current values
3. Modify settings as needed
4. Click "[Save Changes]"
5. Confirmation message shown
6. Service restarts automatically

### Testing Audio
1. Select profile from dropdown
2. Select tone
3. Adjust volume slider
4. Click "[▶ Play]"
5. Audio plays (or error shown)
6. "[⏹ Stop]" available during playback
7. Duration and last-played shown

### Adjusting Quiet Hours
1. Go to Settings
2. Toggle "Enabled" checkbox
3. Set start/end times
4. Add override dates (e.g., holidays)
5. Click "[Save Changes]"
6. System immediately respects new settings

## Accessibility

- High contrast text (#333 on #FFF)
- ARIA labels on all controls
- Keyboard navigation (Tab, Enter, Escape)
- Mobile-friendly touch targets (44px minimum)
- Dark mode support (CSS media query)
- Screen reader compatible

## Performance

- Dashboard loads in < 1s
- Real-time updates via polling (5s interval)
- Modals don't block UI
- Audio test is non-blocking
- No full page reloads
- Minimal JavaScript bundle (~50KB gzipped)

---

This wireframe can be implemented in:
- **HTML/CSS/Vanilla JS** - Minimal dependencies
- **Bootstrap 5** - Responsive grid system
- **Alpine.js** - Lightweight interactivity
- **HTMX** - Smooth dynamic updates
