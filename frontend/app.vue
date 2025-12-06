<template>
  <div class="container">
    <h1>Nhận Diện Vật Thể YOLOv8</h1>
    <div class="video-container">
      <video ref="video" autoplay playsinline muted @loadedmetadata="onVideoLoaded"></video>
      <canvas ref="canvas"></canvas>
    </div>
    <div class="status">
      <p>Trạng thái: {{ status }}</p>
      <p>FPS: {{ fps }}</p>
      <div class="control-group">
        <label>Chọn giọng đọc ({{ voices.length }}):</label>
        <div class="select-wrapper">
          <select v-model="selectedVoiceURI">
            <option v-for="voice in voices" :key="voice.voiceURI" :value="voice.voiceURI">
              {{ voice.name }} ({{ voice.lang }})
            </option>
          </select>
          <button class="icon-btn" @click="loadVoices" title="Tải lại danh sách giọng">↻</button>
        </div>
      </div>
      <button @click="toggleDetection">{{ isDetecting ? 'Dừng' : 'Bắt đầu' }} Nhận diện</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const config = useRuntimeConfig()
const video = ref(null)
const canvas = ref(null)
const status = ref('Đang khởi tạo...')
const isDetecting = ref(false)
const fps = ref(0)
let ws = null
let animationId = null
let lastTime = 0
let lastSpeakTime = 0
const SPEAK_COOLDOWN = 2500 // 2.5 seconds between speaking same object
const audioCache = new Map()

const detectedObjects = new Set()
const lastObjectHeight = ref(0)
const lastObjectClass = ref('')


// Vietnamese translation dictionary
const vnDict = {
  'person': 'người',
  'bicycle': 'xe đạp',
  'car': 'ô tô',
  'motorcycle': 'xe máy',
  'airplane': 'máy bay',
  'bus': 'xe buýt',
  'train': 'tàu hỏa',
  'truck': 'xe tải',
  'boat': 'thuyền',
  'traffic light': 'đèn giao thông',
  'fire hydrant': 'vòi cứu hỏa',
  'stop sign': 'biển báo dừng',
  'parking meter': 'đồng hồ đỗ xe',
  'bench': 'ghế đá',
  'bird': 'chim',
  'cat': 'mèo',
  'dog': 'chó',
  'horse': 'ngựa',
  'sheep': 'cừu',
  'cow': 'bò',
  'elephant': 'voi',
  'bear': 'gấu',
  'zebra': 'ngựa vằn',
  'giraffe': 'hươu cao cổ',
  'backpack': 'ba lô',
  'umbrella': 'ô',
  'handbag': 'túi xách',
  'tie': 'cà vạt',
  'suitcase': 'vali',
  'frisbee': 'đĩa bay',
  'skis': 'ván trượt tuyết',
  'snowboard': 'ván trượt tuyết',
  'sports ball': 'bóng thể thao',
  'kite': 'diều',
  'baseball bat': 'gậy bóng chày',
  'baseball glove': 'găng tay bóng chày',
  'skateboard': 'ván trượt',
  'surfboard': 'ván lướt sóng',
  'tennis racket': 'vợt tennis',
  'bottle': 'chai',
  'wine glass': 'ly rượu',
  'cup': 'cốc',
  'fork': 'nĩa',
  'knife': 'dao',
  'spoon': 'thìa',
  'bowl': 'bát',
  'banana': 'chuối',
  'apple': 'táo',
  'sandwich': 'bánh mì kẹp',
  'orange': 'cam',
  'broccoli': 'súp lơ',
  'carrot': 'cà rốt',
  'hot dog': 'xúc xích',
  'pizza': 'bánh pizza',
  'donut': 'bánh donut',
  'cake': 'bánh ngọt',
  'chair': 'ghế',
  'couch': 'ghế sofa',
  'potted plant': 'cây cảnh',
  'bed': 'giường',
  'dining table': 'bàn ăn',
  'toilet': 'nhà vệ sinh',
  'tv': 'ti vi',
  'laptop': 'máy tính xách tay',
  'mouse': 'chuột máy tính',
  'remote': 'điều khiển từ xa',
  'keyboard': 'bàn phím',
  'cell phone': 'điện thoại',
  'microwave': 'lò vi sóng',
  'oven': 'lò nướng',
  'toaster': 'máy nướng bánh mì',
  'sink': 'bồn rửa',
  'refrigerator': 'tủ lạnh',
  'book': 'sách',
  'clock': 'đồng hồ',
  'vase': 'bình hoa',
  'scissors': 'kéo',
  'teddy bear': 'gấu bông',
  'hair drier': 'máy sấy tóc',
  'toothbrush': 'bàn chải đánh răng'
}

const getVietnameseName = (className) => {
  return vnDict[className] || className
}

const connectWebSocket = () => {
  status.value = 'Đang kết nối đến máy chủ...'
  // Use runtime config for backend URL
  const backendUrl = config.public.backendUrl
  ws = new WebSocket(`${backendUrl}/ws`)

  ws.onopen = () => {
    status.value = 'Đã kết nối'
  }

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)
    if (data.detections) {
      drawDetections(data.detections)
      handleTTS(data.detections)
    }
  }

  ws.onclose = () => {
    status.value = 'Đã ngắt kết nối. Đang thử lại...'
    setTimeout(connectWebSocket, 1000)
  }

  ws.onerror = (error) => {
    console.error('WebSocket error:', error)
    status.value = 'Lỗi kết nối'
  }
}

const startCamera = async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: {
        facingMode: 'environment',
        width: { ideal: 640 },
        height: { ideal: 480 }
      }
    })
    video.value.srcObject = stream
  } catch (err) {
    console.error('Error accessing camera:', err)
    status.value = 'Lỗi camera: ' + err.message
  }
}

const onVideoLoaded = () => {
  if (video.value && canvas.value) {
    canvas.value.width = video.value.videoWidth
    canvas.value.height = video.value.videoHeight
  }
}

const sendFrame = () => {
  if (!isDetecting.value || !ws || ws.readyState !== WebSocket.OPEN || !video.value || !canvas.value) return

  const ctx = canvas.value.getContext('2d')
  // Draw video frame to canvas for processing (or use a separate offscreen canvas)
  // Here we just use the visible canvas to capture the frame, but we'll overwrite it with boxes later
  // To avoid flickering, ideally use an offscreen canvas, but for simplicity:
  
  const offscreenCanvas = document.createElement('canvas')
  // Resize to 320px width for faster transmission and processing
  const scale = 320 / video.value.videoWidth
  offscreenCanvas.width = 320
  offscreenCanvas.height = video.value.videoHeight * scale
  
  const offCtx = offscreenCanvas.getContext('2d')
  offCtx.drawImage(video.value, 0, 0, offscreenCanvas.width, offscreenCanvas.height)
  
  const base64 = offscreenCanvas.toDataURL('image/jpeg', 0.5) // Quality 0.5
  ws.send(base64)
}

const drawDetections = (detections) => {
  const ctx = canvas.value.getContext('2d')
  // Clear previous drawings
  ctx.clearRect(0, 0, canvas.value.width, canvas.value.height)
  
  // We don't need to draw the video again if the video element is visible behind the canvas
  // Just draw boxes
  
  detections.forEach(det => {
    const [x1, y1, x2, y2] = det.bbox
    const vnName = getVietnameseName(det.class)
    const label = `${vnName} (${(det.conf * 100).toFixed(1)}%)`
    
    ctx.strokeStyle = '#00FF00'
    ctx.lineWidth = 2
    ctx.strokeRect(x1, y1, x2 - x1, y2 - y1)
    
    ctx.fillStyle = '#00FF00'
    ctx.font = '16px Arial'
    ctx.fillText(label, x1, y1 - 5)
  })
}

const handleTTS = (detections) => {
  const now = Date.now()
  
  if (!isDetecting.value) {
    lastObjectHeight.value = 0
    lastObjectClass.value = ''
    return
  }

  const confidentDetections = detections.filter(d => d.conf > 0.45)
  
  if (confidentDetections.length > 0) {
    // Sort by confidence (or size - likely the closest object is largest)
    // Heuristic: largest box detected ~ closest object
    confidentDetections.sort((a, b) => {
        const hA = a.bbox[3] - a.bbox[1]
        const hB = b.bbox[3] - b.bbox[1]
        return hB - hA
    })
    
    const topObj = confidentDetections[0]
    const [x1, y1, x2, y2] = topObj.bbox
    const currentHeight = y2 - y1
    const currentClass = topObj.class

    // Calculate percentage change if it's the same object class
    let percentChange = 0
    if (lastObjectClass.value === currentClass && lastObjectHeight.value > 0) {
      percentChange = (currentHeight - lastObjectHeight.value) / lastObjectHeight.value
    }

    // Logic:
    // 1. New object detected (or class changed) -> Speak immediately
    // 2. Same object, but got closer by > 5% -> Speak warning
    
    let shouldSpeak = false
    let text = ""

    if (currentClass !== lastObjectClass.value) {
      // New object logic
      shouldSpeak = true
      text = `Phát hiện ${getVietnameseName(currentClass)}`
      
      // Update reference
      lastObjectClass.value = currentClass
      lastObjectHeight.value = currentHeight
    } else {
        // Same object logic
        if (percentChange > 0.05) {
            // Moved closer by 5%
            shouldSpeak = true
            text = `Cảnh báo, ${getVietnameseName(currentClass)} đang lại gần`
            
            // Update reference to this new closer position so we don't spam unless it gets even closer
            lastObjectHeight.value = currentHeight
        }
    }

    if (shouldSpeak && (now - lastSpeakTime > 1000)) { // 1s minimal cooldown to prevent absolute chaos
        speak(text)
        lastSpeakTime = now
    }
  } else {
    // No detections, reset tracking
    lastObjectHeight.value = 0
    lastObjectClass.value = ''
  }
}

const voices = ref([])
const selectedVoiceURI = ref('')

const loadVoices = () => {
  const allVoices = window.speechSynthesis.getVoices()
  
  // Create online voice option
  const onlineVoice = {
      name: 'Google Vietnamese (Online)',
      lang: 'vi-VN',
      voiceURI: 'online-vi-vn',
      localService: false
  }

  // Sort: Vietnamese first (including online), then English, then others
  voices.value = [onlineVoice, ...allVoices].sort((a, b) => { // Always put online voice or native VN voice first
    const aVi = a.lang.includes('vi')
    const bVi = b.lang.includes('vi')
    if (aVi && !bVi) return -1
    if (!aVi && bVi) return 1
    return 0
  })

  // Auto-select Vietnamese voice if available and not yet selected
  if (!selectedVoiceURI.value) {
     // Prefer native if exists, else online
    const vnVoice = voices.value.find(v => v.lang.includes('vi') && v.voiceURI !== 'online-vi-vn')
    if (vnVoice) {
      selectedVoiceURI.value = vnVoice.voiceURI
    } else {
      selectedVoiceURI.value = 'online-vi-vn' // Fallback to online
    }
  }
}

const speak = (text) => {
  console.log('Speaking:', text)

  // Handle Online Voice
  if (selectedVoiceURI.value === 'online-vi-vn') {
      if (audioCache.has(text)) {
          const cachedAudio = audioCache.get(text)
          cachedAudio.currentTime = 0 // Reset to start
          cachedAudio.play().catch(e => console.error("Cached audio play error:", e))
      } else {
          const url = `https://translate.google.com/translate_tts?ie=UTF-8&q=${encodeURIComponent(text)}&tl=vi&client=tw-ob`
          const audio = new Audio(url)
          audio.onloadeddata = () => {
              audioCache.set(text, audio)
          }
          audio.play().catch(e => console.error("Audio play error:", e))
      }
      return
  }

  // Handle Native Speech Synthesis
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel() // Stop previous

    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = 'vi-VN'
    
    // Use selected voice
    if (selectedVoiceURI.value) {
      const voice = voices.value.find(v => v.voiceURI === selectedVoiceURI.value)
      if (voice) {
        utterance.voice = voice
        console.log('Using voice:', voice.name)
      }
    }

    // Fallback if no voice selected (should unlikely happen with our new logic)
    if (!utterance.voice) {
         const vnVoice = voices.value.find(v => v.lang.includes('vi'))
         if (vnVoice) utterance.voice = vnVoice
    }

    window.speechSynthesis.speak(utterance)
  }
}

const toggleDetection = () => {
  isDetecting.value = !isDetecting.value
  if (isDetecting.value) {
    loop()
  } else {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel()
    }
  }
}

const loop = () => {
  if (!isDetecting.value) return
  
  const now = Date.now()
  if (now - lastTime >= 50) { // Limit to ~20 FPS sending
    sendFrame()
    lastTime = now
  }
  
  animationId = requestAnimationFrame(loop)
}

onMounted(() => {
  startCamera()
  connectWebSocket()
  
  // Load voices
  if ('speechSynthesis' in window) {
    loadVoices()
    window.speechSynthesis.onvoiceschanged = loadVoices
  }
})

onUnmounted(() => {
  if (ws) ws.close()
  if (animationId) cancelAnimationFrame(animationId)
  if (video.value && video.value.srcObject) {
    video.value.srcObject.getTracks().forEach(track => track.stop())
  }
})
</script>

<style>
.container {
  display: flex;
  flex-direction: column;
  align-items: center;
  font-family: sans-serif;
  padding: 20px;
}

.video-container {
  position: relative;
  width: 640px;
  height: 480px;
  background: #000;
  margin-bottom: 20px;
}

video {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.status {
  text-align: center;
  display: flex;
  flex-direction: column;
  gap: 10px;
  align-items: center;
}

.control-group {
  margin: 10px 0;
}

.select-wrapper {
  display: flex;
  align-items: center;
  gap: 5px;
}

select {
  padding: 8px;
  border-radius: 4px;
  border: 1px solid #ddd;
  max-width: 200px;
}

.icon-btn {
  padding: 5px 10px;
  background: #2196F3;
  margin-left: 0;
}

button {
  padding: 10px 20px;
  font-size: 16px;
  cursor: pointer;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 5px;
}

button:hover {
  background-color: #45a049;
}
</style>
