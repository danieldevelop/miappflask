/**
 * Captura de cámara y detección facial en tiempo real.
 * Fase 2.2A
 */

// Usar IIFE para evitar redeclaración si el script se carga múltiples veces
(function() {
    'use strict';

    // Si ya está definida, no redefinir
    if (typeof window.FacialCameraCapture !== 'undefined') {
        console.log('FacialCameraCapture ya cargada, saltando...');
        return;
    }

class FacialCameraCapture {
    constructor() {
        this.video = null;
        this.canvas = null;
        this.stream = null;
        this.isCapturing = false;
        this.detectionInterval = null;
    }

    async init(videoElementId, canvasElementId) {
        this.video = document.getElementById(videoElementId);
        this.canvas = document.getElementById(canvasElementId);

        if (!this.video || !this.canvas) {
            throw new Error("No se encontraron elementos de video/canvas");
        }

        try {
            this.stream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: "user", width: { ideal: 640 }, height: { ideal: 480 } },
                audio: false
            });

            this.video.srcObject = this.stream;

            // Esperar a que el video esté listo antes de reproducir
            await new Promise(resolve => {
                this.video.onloadedmetadata = () => {
                    this.video.play().catch(err => console.error("Error al reproducir video:", err));
                    resolve();
                };
            });

            this.isCapturing = true;

            return true;
        } catch (error) {
            console.error("Error al acceder a la cámara:", error);
            throw new Error("No se pudo acceder a la cámara. Verifica permisos.");
        }
    }

    startDetection(onFrameCallback) {
        if (!this.isCapturing) {
            console.warn("Cámara no está inicializada");
            return;
        }

        this.detectionInterval = setInterval(() => {
            const ctx = this.canvas.getContext("2d");
            ctx.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);
            const frameData = this.canvas.toDataURL("image/jpeg");

            if (onFrameCallback) {
                onFrameCallback(frameData);
            }
        }, 200);
    }

    stopDetection() {
        if (this.detectionInterval) {
            clearInterval(this.detectionInterval);
            this.detectionInterval = null;
        }
    }

    stop() {
        this.stopDetection();

        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }

        this.isCapturing = false;
    }

    captureFrame() {
        const ctx = this.canvas.getContext("2d");
        ctx.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);
        return this.canvas.toDataURL("image/jpeg");
    }
}


    // Exportar para uso en módulos
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = FacialCameraCapture;
    }

    // Asegurar disponibilidad global en navegador
    if (typeof window !== 'undefined') {
        window.FacialCameraCapture = FacialCameraCapture;
    }

})();

