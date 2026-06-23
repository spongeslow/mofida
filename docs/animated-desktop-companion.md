# Moufida – Animated Desktop Companion Feature
## Overview

This feature introduces a living, breathing 2D animated character named Moufida that resides on the user's desktop, transforming the application from a traditional tool into a companion that entrepreneurs interact with throughout their day.

The character brings personality, warmth, and emotional connection to the entrepreneurial journey – making the experience of building a startup feel less solitary and more engaging. It's inspired by desktop companions like Microsoft Office's Clippy (but actually useful), desktop pets like Shimeji, and modern AI assistants.

## Core Concept

A Living Companion on Your Desktop

Moufida (the 2D animated character) lives on the user's desktop, roaming freely in the lower-right corner of the screen. She is always present, always watching, always ready to help – just like a real co-founder sitting next to you.

The character is designed to be:

- Friendly and approachable – A female character with "Moufida" displayed above her head.

- Always present – Roaming the desktop even when the overlay is closed.

- Interactive – Reacts to voice commands, clicks, and system events.

- Expressively animated – Different movements for different states (idle, thinking, listening, speaking, startled).

## Why this Feature Matters

| Benefit | Reason |
|---------|--------|
| Emotional connection | Entrepreneurs often work alone – having a "companion" reduces isolation |
| Memorable UX | Users will remember Moufida long after using other startup tools |
| Gentle engagement | The character doesn't demand attention; she's just there when needed |
| State visualization | Users can see at a glance whether Moufida is listening, thinking, or speaking |
| Brand differentiator | No other hackathon project has a living desktop companion |
| Delight factor | Judges and users will appreciate the creativity and attention to detail |

## Character Design & Behaviour 

### Physical Presence

- Location: Lower-right corner of the desktop, roaming freely.
- Size: Approximately 100-150 pixels tall (scalable).
- Style: 2D illustrated character (vector art, warm colors).
- Note that you can search the web for free assets for moufida character (you can choose a character that has movements that we can use in our usecase)
- Name Display: "Moufida" floating above her head.
- Transparency: Semi-transparent when idle, fully opaque when active.

## Desktop Behavior

| State | Animation | Description |
|-------|-----------|-------------|
| Idle Roaming | Gentle walking in place, slight bobbing | She's just hanging out, waiting to be called |
| Waking Up | Startled jump, eyes widen | Triggered by "Hey Moufida" or a click |
| Listening | Leaning forward, head tilted, ears visibly perked | She's actively listening for commands |
| Thinking | Scratching head, looking upward, foot tapping | Processing a complex question or generating a response |
| Speaking | Mouth moving with speech, expressive gestures | Reading out the response via TTS |
| Processing | Loading spinner / thinking animation | Waiting for the backend to respond |
| Alerting | Jumping up, waving arms | A critical alert has been detected |
| Sleeping | Gentle breathing, eyes closed | After "Goodnight Moufida" command |
| Celebrating | Happy dance, fists in the air | Milestone achieved! |

## Trigger Events

| Event | Character Reaction |
|-------|--------------------|
| "Hey Moufida" (wake word) | Startled jump → opens overlay → transitions to listening |
| Click on character | Startled jump → opens overlay → transitions to listening |
| Voice command given | Transitions to listening → thinking → speaking |
| Response ready | Speaking animation while TTS plays |
| "Goodnight Moufida" | Closes overlay → transitions to sleeping on desktop |
| Critical alert detected | Alert animation (jump, wave arms) → notification |
| Score improvement | Subtle happy wiggle |
| Milestone completed | Celebration dance |

## In-App Character Animation

Inside the desktop app overlay, the character appears as an integrated avatar with state-based animations:
### Overlay States

| State | Character Animation | Purpose |
|-------|---------------------|---------|
| Idle | Gently swaying, looking around | Waiting in the corner of the overlay |
| Listening | Leaning forward, ear perked, head tilted | User is speaking (Voice Activity Detection active) |
| Thinking | Scratching head, looking up, tapping foot | Backend is processing the request |
| Speaking | Mouth moving in sync with TTS, gesturing | Reading the response aloud |
| Processing | Pacing back and forth | Waiting for long-running operations |
| Alert | Jumping up, pointing at the alert | A critical notification has arrived |

### Character Position in UI

- **Overlay**: Lower-right corner of the chat panel
- **Dashboard**: Mascot icon in the header, full character in a dedicated "About" section
- **Mon Parcours**: Character celebrates when milestones are reached

## Color Palette: Warm Autumn Theme

The Warm Autumn color palette creates a welcoming, professional, and emotionally comforting environment – perfect for the long, often stressful journey of building a startup.
### Palette Overview

| Element | Color Name | Hex | Purpose |
|---------|------------|-----|---------|
| Background | Cream Beige | #F5EBDD | Main app background, warmth and openness |
| Surface | Warm Sand | #E6D5C3 | Cards, panels, secondary surfaces |
| Primary | Coffee Brown | #6F4E37 | Headers, buttons, primary actions |
| Secondary | Milk Chocolate | #8B5E3C | Secondary buttons, accents, highlights |
| Accent | Fallen Leaves Orange | #C96A2D | CTAs, important elements, energy |
| Accent Hover | Autumn Gold | #D98A3A | Hover states, active elements |
| Text | Dark Espresso | #2C1E17 | Body text, labels, readable content |

### Design Meaning

| Color | Psychological Meaning | Why It Works for Moufida |
|-------|----------------------|---------------------------|
| Cream Beige (#F5EBDD) | Warmth, comfort, openness | Makes the app feel welcoming, like a cozy office |
| Coffee Brown (#6F4E37) | Trust, stability, craftsmanship | Builds confidence in Moufida's recommendations |
| Milk Chocolate (#8B5E3C) | Friendliness, richness | Makes the interface feel approachable and generous |
| Fallen Leaves Orange (#C96A2D) | Energy, creativity, action | Draws attention to important actions and CTAs |
| Autumn Gold (#D98A3A) | Highlights, hover states | Provides subtle feedback on interactive elements |
| Dark Espresso (#2C1E17) | Elegance, readability | Ensures text is clear and professional |

### Palette Application

| UI Element | Color |
|------------|-------|
| Main background | #F5EBDD (Cream Beige) |
| Sidebar / Navigation | #E6D5C3 (Warm Sand) |
| Cards / Panels | #E6D5C3 (Warm Sand) with #F5EBDD edges |
| Primary buttons | #6F4E37 (Coffee Brown) |
| Secondary buttons | #8B5E3C (Milk Chocolate) |
| CTA / Important actions | #C96A2D (Fallen Leaves Orange) |
| Hover states | #D98A3A (Autumn Gold) |
| Body text | #2C1E17 (Dark Espresso) |
| Headers | #6F4E37 (Coffee Brown) |
| Accents / Highlights | #C96A2D (Fallen Leaves Orange) |

## Why Warm Autumn?

- Reduces visual fatigue – Warm, muted tones are easier on the eyes during long work sessions.
- Conveys trust – Brown tones are associated with reliability and craftsmanship.
- Encourages creativity – Orange accents stimulate energy and innovative thinking.
- Feels Tunisian – The warm, earthy tones reflect the Tunisian landscape and culture.
- Differentiates – Most tech products use blue/cool palettes; Moufida stands out.

