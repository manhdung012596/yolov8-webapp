# YOLOv8 Real-time Object Detection Web App

Ứng dụng web nhận diện vật thể real-time sử dụng YOLOv8, với giao diện tiếng Việt và text-to-speech.

## Tech Stack

**Backend:**
- FastAPI
- YOLOv8 (Ultralytics)
- WebSocket
- OpenCV

**Frontend:**
- Nuxt 3
- Vue 3
- WebRTC (Camera access)

## Deployment

- Backend: Railway
- Frontend: Vercel

## Local Development

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Environment Variables

### Frontend (.env.production)
```
NUXT_PUBLIC_BACKEND_URL=wss://your-backend-url.railway.app
```
