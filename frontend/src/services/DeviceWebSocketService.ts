// DeviceWebSocketService.ts
// Service for connecting and streaming audio to TeachSense backend via WebSocket

export interface DeviceWebSocketOptions {
  deviceId: number;
  deviceToken: string;
  deviceType?: string; // e.g., 'audio_input'
  onMessage?: (msg: unknown) => void;
  onOpen?: () => void;
  onError?: (err: Event) => void;
  onClose?: (ev: CloseEvent) => void;
}

export class DeviceWebSocketService {
  private ws: WebSocket | null = null;
  private options: DeviceWebSocketOptions;
  private reconnectAttempts = 0;
  private maxRetries = 5;

  constructor(options: DeviceWebSocketOptions) {
    this.options = options;
    this.connect();
  }

  private connect() {
    const { deviceId, deviceToken, onMessage, onOpen, onError, onClose, deviceType } = this.options;
    this.ws = new WebSocket(
      `wss://teachsense.onrender.com/ws/devices/${deviceId}/?token=${deviceToken}`
    );
    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
      this.sendHandshake(deviceId, deviceType || 'audio_input');
      onOpen?.();
    };
    this.ws.onmessage = (event) => {
      const msg: unknown = JSON.parse(event.data);
      onMessage?.(msg);
    };
    this.ws.onerror = (err) => {
      onError?.(err);
    };
    this.ws.onclose = (ev) => {
      onClose?.(ev);
      this.autoReconnect();
    };
  }

  private autoReconnect() {
    if (this.reconnectAttempts < this.maxRetries) {
      setTimeout(() => {
        this.reconnectAttempts++;
        this.connect();
      }, Math.pow(2, this.reconnectAttempts) * 1000);
    }
  }

  private sendHandshake(deviceId: number, deviceType: string) {
    this.send({
      type: 'handshake',
      device_id: deviceId,
      device_type: deviceType,
      protocol_version: '1.0',
      timestamp: new Date().toISOString(),
    });
  }

  public send(data: unknown) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  public close() {
    this.ws?.close();
  }
}

// Utility to stream audio from mic and send frames
type AudioStreamOptions = {
  wsService: DeviceWebSocketService;
  sampleRate?: number;
  channels?: number;
  bitDepth?: number;
};

export async function streamMicrophoneAudio({ wsService, sampleRate = 48000, channels = 1, bitDepth = 16 }: AudioStreamOptions) {
  const audioContext = new window.AudioContext({ sampleRate });
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  const source = audioContext.createMediaStreamSource(stream);
  const processor = audioContext.createScriptProcessor(4096, channels, channels);
  let frameNumber = 0;

  processor.onaudioprocess = (e) => {
    for (let ch = 0; ch < channels; ch++) {
      const audioData = e.inputBuffer.getChannelData(ch);
      const uint8 = new Uint8Array(audioData.buffer);
      const data_base64 = btoa(String.fromCharCode(...uint8));
      wsService.send({
        type: 'audio_frame',
        frame_number: frameNumber++,
        timestamp: new Date().toISOString(),
        sample_rate: sampleRate,
        channels,
        bit_depth: bitDepth,
        data_base64,
      });
    }
  };

  source.connect(processor);
  processor.connect(audioContext.destination);

  return { audioContext, stream, processor };
}
