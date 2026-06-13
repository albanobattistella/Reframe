Markdown

# Reframe 🎬📐

Das selbstgehostete "Stirling-PDF" für deine Social-Media-Videos.

**Reframe** ist eine leichtgewichtige, Docker-basierte Web-Anwendung, mit der du deine Videos (z. B. 16:9 Aufnahmen, Streams oder Clips) im Handumdrehen für Social-Media-Plattformen (9:16 Reels/TikTok, 1:1 Instagram Feed etc.) zuschneiden kannst. Komplett lokal, ohne Cloud-Zwang und mit voller Kontrolle über deine Daten.

---

## 🔥 Features

* **Einfacher Upload & visuelles Cropping:** Wirf dein Video rein und wähle den perfekten Bildausschnitt.
* **Social-Media-Presets:** Vordefinierte Formate für alle gängigen Plattformen:
  * `9:16` (TikTok, YouTube Shorts, Instagram Reels)
  * `1:1` (Instagram Feed, LinkedIn)
  * `4:5` (Instagram Post optimiert)
* **FFmpeg Powerhouse:** Schnelles, verlustfreies oder präzises Transcoding direkt im Backend.
* **100% Self-Hosted:** Perfekt fürs Homelab. Keine externen APIs, keine Datenspionage, keine Abogebühren.
* **Docker Ready:** Mit einem einzigen Befehl startklar.

---

## 🛠 Tech Stack

Dieses Projekt ist so aufgebaut, dass es maximale Performance mit einer einfachen Codebasis vereint:

* **Backend:** Python mit **FastAPI** (asynchrone API-Endpunkte für schnelles Datei-Handling)
* **Video-Processing:** **FFmpeg** (der Goldstandard für Videomanipulation)
* **Frontend:** Ein sauberes, schlankes UI (z. B. Vanilla JS oder Svelte/Vue) ohne überladene Framework-Voraussetzungen
* **Deployment:** **Docker** & **Docker Compose**

---

## 🚀 Schnellstart (Docker Compose)

Sobald das Image bereit ist, reicht eine einfache `docker-compose.yml`:

```yaml
version: '3.8'

services:
  reframe:
    image: ghcr.io/dein-username/reframe:latest
    container_name: reframe
    ports:
      - "8080:8080"
    volumes:
      - ./media/uploads:/app/uploads
      - ./media/exports:/app/exports
    restart: unless-stopped

🗺️ Roadmap / Geplante Features

Der Fokus liegt zuerst auf einer bombenfesten Basisfunktionalität. Danach folgen:

    [ ] Smart Tracking (AI-Auto-Crop): Automatische Gesichtserkennung via YOLOv8, um das Motiv im Fokus zu behalten.

    [ ] Lokale Untertitel (Whisper Integration): KI-generierte Untertitel, die direkt ins Video eingebrannt werden.

    [ ] Audio-Normalisierung: Automatische Anpassung der Lautstärke für Social Media.

    [ ] Custom Overlays: Logos oder Wasserzeichen direkt beim Export einbinden.
