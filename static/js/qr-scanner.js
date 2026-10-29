/**
 * HoneyChain - Browser Camera QR Code Scanner (qr-scanner.js)
 */

let videoStream = null;
let animationFrameId = null;

function initQrScanner() {
  const video = document.getElementById("qrVideo");
  const canvas = document.getElementById("qrCanvas");
  const startBtn = document.getElementById("startCameraBtn");
  const stopBtn = document.getElementById("stopCameraBtn");
  const cameraSelect = document.getElementById("cameraSelect");
  const scannerStatus = document.getElementById("scannerStatus");
  const scanOverlay = document.getElementById("scanOverlay");

  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    if (scannerStatus) {
      scannerStatus.textContent = "Camera API not supported in this browser. Please use manual batch lookup below.";
      scannerStatus.className = "alert-message alert-error";
    }
    if (startBtn) startBtn.disabled = true;
    return;
  }

  // Populate camera options
  navigator.mediaDevices.enumerateDevices().then(devices => {
    const videoDevices = devices.filter(d => d.kind === "videoinput");
    if (cameraSelect && videoDevices.length > 0) {
      cameraSelect.innerHTML = "";
      videoDevices.forEach((device, idx) => {
        const opt = document.createElement("option");
        opt.value = device.deviceId;
        opt.text = device.label || `Camera ${idx + 1}`;
        cameraSelect.appendChild(opt);
      });
    }
  }).catch(err => {
    console.warn("Could not list video devices:", err);
  });

  async function startCamera() {
    try {
      const selectedDeviceId = cameraSelect ? cameraSelect.value : null;
      const constraints = {
        video: selectedDeviceId ? { deviceId: { exact: selectedDeviceId } } : { facingMode: "environment" }
      };

      videoStream = await navigator.mediaDevices.getUserMedia(constraints);
      if (video) {
        video.srcObject = videoStream;
        video.setAttribute("playsinline", true);
        await video.play();
      }

      if (scannerStatus) {
        scannerStatus.textContent = "Camera active. Align HoneyChain QR code within frame...";
        scannerStatus.className = "alert-message alert-info";
      }

      if (startBtn) startBtn.style.display = "none";
      if (stopBtn) stopBtn.style.display = "inline-flex";
      if (scanOverlay) scanOverlay.style.display = "block";

      scanFrame();
    } catch (err) {
      console.error("Camera access error:", err);
      if (scannerStatus) {
        scannerStatus.textContent = "Camera access denied or unavailable. You can enter the Batch ID manually below.";
        scannerStatus.className = "alert-message alert-error";
      }
    }
  }

  function stopCamera() {
    if (videoStream) {
      videoStream.getTracks().forEach(track => track.stop());
      videoStream = null;
    }
    if (animationFrameId) {
      cancelAnimationFrame(animationFrameId);
      animationFrameId = null;
    }
    if (video) video.srcObject = null;
    if (startBtn) startBtn.style.display = "inline-flex";
    if (stopBtn) stopBtn.style.display = "none";
    if (scanOverlay) scanOverlay.style.display = "none";
    if (scannerStatus) {
      scannerStatus.textContent = "Camera stopped.";
      scannerStatus.className = "alert-message alert-info";
    }
  }

  function scanFrame() {
    if (!video || video.readyState !== video.HAVE_ENOUGH_DATA) {
      animationFrameId = requestAnimationFrame(scanFrame);
      return;
    }

    if (canvas) {
      const ctx = canvas.getContext("2d", { willReadFrequently: true });
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

      // Check if BarcodeDetector API is natively supported in Chromium
      if ("BarcodeDetector" in window) {
        const detector = new window.BarcodeDetector({ formats: ["qr_code"] });
        detector.detect(canvas).then(barcodes => {
          if (barcodes.length > 0) {
            handleScannedResult(barcodes[0].rawValue);
            return;
          }
          animationFrameId = requestAnimationFrame(scanFrame);
        }).catch(() => {
          animationFrameId = requestAnimationFrame(scanFrame);
        });
        return;
      }
    }

    animationFrameId = requestAnimationFrame(scanFrame);
  }

  function handleScannedResult(content) {
    stopCamera();
    if (scannerStatus) {
      scannerStatus.textContent = "QR Code detected! Redirecting to traceability...";
      scannerStatus.className = "alert-message alert-success";
    }

    // If QR contains a URL with batch_id or path
    let batchId = content.trim();
    if (content.includes("/trace/")) {
      const parts = content.split("/trace/");
      batchId = parts[parts.length - 1].split("?")[0].replace("/", "");
    } else if (content.includes("batch_id=")) {
      const urlObj = new URL(content);
      batchId = urlObj.searchParams.get("batch_id");
    }

    window.location.href = `/trace/${encodeURIComponent(batchId)}`;
  }

  if (startBtn) startBtn.addEventListener("click", startCamera);
  if (stopBtn) stopBtn.addEventListener("click", stopCamera);
  if (cameraSelect) cameraSelect.addEventListener("change", () => {
    if (videoStream) {
      stopCamera();
      startCamera();
    }
  });
}

document.addEventListener("DOMContentLoaded", initQrScanner);

