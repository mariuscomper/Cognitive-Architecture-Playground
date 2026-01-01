# Stoicism Presentation Web App

An interactive, modern web application for viewing the Stoicism: Philosophy for Modern Resilience presentation.

## Features

### 🎯 Core Features
- **Smooth Navigation**: Navigate between slides with beautiful transitions
- **Multiple Input Methods**:
  - Click navigation arrows
  - Keyboard shortcuts (arrow keys, space, Page Up/Down)
  - Touch/swipe gestures on mobile
  - Overview mode for quick access
- **Progress Tracking**: Visual progress bar and slide counter
- **Fullscreen Mode**: Distraction-free presentation view
- **Responsive Design**: Works perfectly on desktop, tablet, and mobile

### ⌨️ Keyboard Shortcuts
- `→` or `Space` or `Page Down` - Next slide
- `←` or `Page Up` - Previous slide
- `Home` - Go to first slide
- `End` - Go to last slide
- `Esc` - Toggle overview mode
- `F` - Toggle fullscreen mode

### 📱 Mobile Support
- Swipe left/right to navigate between slides
- Touch-optimized interface
- Responsive font sizes and layouts

### 🎨 Design Features
- Clean, modern interface with smooth animations
- Stoic color palette (bronze, sage, charcoal)
- Beautiful typography using Quattrocento and Oranienbaum fonts
- Dark theme for comfortable viewing

## Quick Start

### Option 1: Python Server (Recommended)

```bash
# Start the server (opens browser automatically)
python3 server.py

# Or use the system Python
python server.py
```

The server will start at `http://localhost:8000` and automatically open in your browser.

### Option 2: Node.js Server

```bash
# Install a simple server (one-time)
npm install -g http-server

# Run the server
http-server -p 8000

# Open http://localhost:8000 in your browser
```

### Option 3: Direct File Access

Simply open `index.html` in your web browser. Note: Some browsers may block loading `presentation_data.json` due to CORS restrictions when opening files directly. Use a local server (Options 1 or 2) if you encounter issues.

## File Structure

```
.
├── index.html                  # Main HTML structure
├── app.js                     # JavaScript application logic
├── presentation_data.json     # Slide content data
├── server.py                  # Python local server
└── PRESENTATION_README.md     # This file
```

## Usage Guide

### Basic Navigation
1. **Next Slide**: Click the right arrow or press `→` or `Space`
2. **Previous Slide**: Click the left arrow or press `←`
3. **Overview**: Click the "Overview" button or press `Esc`
4. **Fullscreen**: Click the "Fullscreen" button or press `F`

### Overview Mode
- Press `Esc` or click "Overview" to see all slides at once
- Click any slide thumbnail to jump directly to it
- Shows current slide with a highlighted border
- Press `Esc` again or click "Close" to exit

### Fullscreen Mode
- Press `F` or click "Fullscreen" for distraction-free viewing
- Navigation controls remain available
- Press `F` again or `Esc` to exit fullscreen

### Mobile/Touch
- Swipe left for next slide
- Swipe right for previous slide
- Tap navigation arrows
- All buttons are touch-optimized

## Content Overview

The presentation includes 19 slides covering:

1. **The Foundation** (Slides 1-9)
   - Introduction to Stoicism
   - Historical timeline
   - Key Stoic philosophers
   - Four Cardinal Virtues
   - Dichotomy of Control

2. **The Practice** (Slides 10-14)
   - Daily Stoic exercises
   - Premeditatio Malorum
   - Morning and evening routines
   - Prosoche (mindfulness)
   - Stoic journaling

3. **The Science** (Slides 15-18)
   - Stoicism and CBT
   - Research evidence
   - Digital Stoicism
   - Real-world applications

4. **Conclusion** (Slide 19)
   - The Stoic path forward

## Customization

### Changing Colors
Edit the CSS variables in `index.html`:
```css
:root {
    --primary: #C49A6C;    /* Bronze */
    --secondary: #5C6D67;  /* Sage */
    --bg: #2B2B2B;         /* Dark gray */
    --text: #E0DCD7;       /* Light beige */
    --accent: #A8A39D;     /* Gray */
}
```

### Modifying Content
Edit `presentation_data.json` to update slide content. The structure is straightforward:
```json
{
  "metadata": { ... },
  "slides": [
    {
      "slideNumber": 1,
      "type": "cover",
      "title": "Your Title",
      ...
    }
  ]
}
```

### Adding Slides
1. Add a new slide object to the `slides` array in `presentation_data.json`
2. The app will automatically detect and render it
3. Supported slide types: `cover`, `table_of_contents`, `chapter`, `content`, `final`

## Browser Compatibility

- ✅ Chrome/Edge (recommended)
- ✅ Firefox
- ✅ Safari
- ✅ Mobile browsers (iOS Safari, Chrome Android)

## Troubleshooting

### Presentation doesn't load
- Make sure `presentation_data.json` is in the same directory as `index.html`
- Use a local server instead of opening the file directly
- Check browser console for errors (F12)

### Styles look broken
- Ensure internet connection for Google Fonts and FontAwesome
- Try clearing browser cache
- Check that all CSS is loading properly

### Navigation not working
- Make sure JavaScript is enabled in your browser
- Try refreshing the page
- Check browser console for errors

## Development

The app is built with vanilla JavaScript - no frameworks or build tools required!

### Technologies Used
- HTML5
- CSS3 (with CSS Grid and Flexbox)
- Vanilla JavaScript (ES6+)
- Google Fonts (Quattrocento, Oranienbaum, Quattrocento Sans)
- FontAwesome Icons

### Code Structure
- `index.html` - Structure and styling
- `app.js` - Main application class with navigation logic
- `presentation_data.json` - Content data (separated for easy editing)

## Tips for Best Experience

1. **Use fullscreen mode** for presentations
2. **Practice keyboard shortcuts** for smooth presenting
3. **Use overview mode** to quickly jump between sections
4. **Test on your presentation screen** before presenting
5. **Keep overview open** on a second monitor to see all slides

## Credits

- **Content**: Stoicism - Philosophy for Modern Resilience
- **Design**: Modern minimalist approach with Stoic aesthetics
- **Fonts**: Quattrocento, Oranienbaum (Google Fonts)
- **Icons**: FontAwesome

---

Enjoy your presentation! 🏛️
