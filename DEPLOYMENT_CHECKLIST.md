# Deployment & Testing Checklist

## ✅ Backend (Render) - Status: Ready

- [x] Backend code pushed to GitHub (`main` branch)
- [x] `render.yaml` configured with:
  - Root directory: `backend`
  - Build command: `pip install -r requirements.txt`
  - Start command: `uvicorn emotion_api:app --host 0.0.0.0 --port $PORT`
  - Python 3.11
- [x] API URL: `https://emotion-api-0j9z.onrender.com`

### To trigger Render redeploy:
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Select the "emotion-api" service
3. Click **"Deploy latest commit"** (or commit will auto-trigger)

---

## ✅ Expo App (Mobile) - Status: Ready for Build

### Features Updated:
- **Front camera** directly opened (not rear)
- **5-second video capture** (matches original project logic)
- **Proper FormData** payload with native file metadata
- **Live API connection** to: `https://emotion-api-0j9z.onrender.com`

### Files Modified:
- `mobile_app/App.tsx` - Frontend logic
- `mobile_app/.env` - API URL configured
- `mobile_app/app.json` - App metadata
- `mobile_app/eas.json` - Build config

---

## 🚀 Android APK Build (Recommended)

```bash
cd mobile_app
npm install
eas build --platform android --profile preview
```

This produces a direct APK file for sideload or distribution.

### Once the APK is ready:
1. Download the APK from the EAS build dashboard
2. Email it to your phone or transfer via QR code
3. Install: **Settings → Apps → Install Unknown Apps** → select APK

---

## 📱 Testing on Device

### Pre-test checklist:
- [ ] Backend is live at `https://emotion-api-0j9z.onrender.com/health` (should return `{"status":"ok"}`)
- [ ] `.env` file contains correct API URL
- [ ] APK is installed on Android device
- [ ] Camera permissions granted to the app

### Workflow to test:
1. **Open app** on phone
2. **Click "Front Camera"**
3. **Record a 5-second face video** (clearly face toward camera)
4. **Click "Generate Emotion"**
5. **Check result:**
   - If face detected: emotion + confidence
   - If no face: "Unknown" + message to rerecord

---

## 🔧 Backend Fallback

If models fail to load in production, backend returns a demo result:
```json
{
  "emotion": "Happy",
  "confidence": 0.82,
  "message": "Model not fully loaded; demo prediction used.",
  "fallback": true
}
```

This keeps the API live even if dependencies are missing.

---

## 📝 Git Status

- **Latest commit:** "Updated backend (5-second video support) and app (front camera + proper FormData)"
- **Branch:** `main`
- **Remote:** `origin` → GitHub
- **Status:** All changes pushed ✅

---

## 🎯 Next Steps

1. **Verify Render redeploy** (watch logs for any errors)
2. **Build Android APK** using EAS CLI
3. **Install APK on test device**
4. **Record a video and test emotion prediction**
5. **(Optional) If working, distribute APK to users**

---

## 📞 Common Issues & Fixes

| Issue | Fix |
|-------|-----|
| App shows "Network Error" | Check `/health` endpoint; ensure API is online |
| "No face detected" error | Record with clear front-facing view, good lighting |
| Camera permission denied | Grant camera access in phone settings → App Permissions |
| APK won't install | Enable "Install from Unknown Sources" in settings |
| Render service down | Check Render dashboard; redeploy if needed |

---

**Last Updated:** Sept 8, 2026  
**Backend URL:** https://emotion-api-0j9z.onrender.com  
**App Flow:** Front camera → 5-sec video → Upload → Emotion result
