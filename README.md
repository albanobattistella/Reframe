# Reframe 🎬📐

The self-hosted "Stirling-PDF" for your social media videos.

**Reframe** is a lightweight, Docker-based web application that lets you easily crop, trim, and format your videos (e.g., 16:9 recordings, streams, or clips) for social media platforms (9:16 Reels/TikTok, 1:1 Instagram Feed, etc.) in a flash. Completely local, no cloud dependencies, and with full control over your data.

![Reframe Screenshot](./assets/reframe-screenshot.png)

---

## 🔥 Features

* **Visual Cropping & Formatting**: Drop your video in and choose the perfect crop. Includes presets for:
  * `9:16` (TikTok, YouTube Shorts, Instagram Reels)
  * `1:1` (Instagram Feed, LinkedIn)
  * `4:5` (Instagram Portrait)
  * `Custom` (Freeform aspect ratio)
* **Batch Processing**: Need to process multiple videos? Use the batch processor to apply crop, trim, and overlay settings to all videos at once!
* **Watermarks & Overlays**: Add your custom logo or watermark. You can also add custom text overlays with adjustable fonts, colors, and drop shadows!
* **Video Trimming**: Precisely trim the start and end times of your videos.
* **Hardware Acceleration (GPU)**: Leverage hardware acceleration for blazing-fast exports.
* **Save & Share Configurations**: Export your favorite configurations and import them later so you don't have to dial in your settings every time.
* **Built-in Media Manager**: Manage, view, and bulk-delete your uploaded media and exported videos right within the app.
* **Multi-Language Support**: Available in English, German, Spanish, and French.
* **Light & Dark Mode**: A beautiful, modern UI that seamlessly switches between light and dark mode.
* **100% Self-Hosted & Local**: FFmpeg powerhouse running locally on your hardware. No external APIs, no data spying, no subscriptions.

---

## 🛠 Tech Stack

Built for maximum performance and a simple, maintainable codebase:

* **Backend:** Python with **FastAPI** (asynchronous API endpoints for fast file handling)
* **Video Processing:** **FFmpeg** (the gold standard for video manipulation)
* **Frontend:** Built with **Vue 3** + Vite for a sleek, responsive UI
* **Deployment:** **Docker** & **Docker Compose**

---

## 🚀 Quick Start (Docker Compose)

Get up and running with a single `docker-compose.yml`:

```yaml
version: '3.8'

services:
  reframe:
    image: ghcr.io/your-username/reframe:latest
    container_name: reframe
    ports:
      - "8080:8080"
    volumes:
      - ./media/uploads:/app/uploads
      - ./media/exports:/app/exports
    restart: unless-stopped
```

---

## 🗺️ Roadmap / Planned Features

* [ ] **Smart Tracking (AI Auto-Crop):** Automatic face detection via YOLOv8 to keep the subject in focus.
* [ ] **Local Subtitles (Whisper Integration):** AI-generated subtitles baked directly into the video.
* [ ] **Audio Normalization:** Automatic volume adjustment for social media.
