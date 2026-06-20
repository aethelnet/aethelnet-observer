export type EventCallback = (data: any) => void;

class LgnnEventRouter {
  private updatePending = false;
  private updateCallbacks: (() => void)[] = [];
  
  private batchBuffer: any[] = [];
  private batchTickPending = false;

  constructor() {}

  /**
   * Ingest raw WebSocket messages and route them efficiently
   */
  public ingest(rawEvent: MessageEvent) {
    if (rawEvent.data === 'update') {
      this.scheduleGraphUpdate();
    } else {
      try {
        const data = JSON.parse(rawEvent.data);
        if (data.type === 'global_event') {
          this.bufferGlobalEvent(data);
        } else if (data.type === 'telemetry') {
          this.scheduleGraphUpdate();
        }
      } catch (e) {
        // Not JSON, ignore or log
      }
    }
  }

  /**
   * Debounces and throttles 'update' events.
   * Prevents 100 users triggering 100 API fetches simultaneously.
   * Limits graph re-fetches to a maximum of 4 times per second (250ms).
   */
  private scheduleGraphUpdate() {
    if (this.updatePending) return;
    this.updatePending = true;
    
    setTimeout(() => {
      this.updatePending = false;
      this.updateCallbacks.forEach(cb => cb());
    }, 250);
  }

  public onGraphUpdate(cb: () => void) {
    this.updateCallbacks.push(cb);
  }

  public offGraphUpdate(cb: () => void) {
    this.updateCallbacks = this.updateCallbacks.filter(c => c !== cb);
  }

  /**
   * Buffers global events and flushes them efficiently on the next animation frame.
   * Reduces Vue reactivity thrashing.
   */
  private bufferGlobalEvent(data: any) {
    this.batchBuffer.push(data);
    if (!this.batchTickPending) {
      this.batchTickPending = true;
      requestAnimationFrame(() => this.flushBatch());
    }
  }

  private flushBatch() {
    this.batchTickPending = false;
    if (this.batchBuffer.length === 0) return;
    
    const eventsToProcess = [...this.batchBuffer];
    this.batchBuffer = [];

    // Dispatch processed batch. We still use window CustomEvent 
    // to maintain compatibility with decoupled Vue components.
    eventsToProcess.forEach(evt => {
       window.dispatchEvent(new CustomEvent('aethel-global-event', { detail: evt }));
    });
  }
}

// Export a singleton instance
export const eventRouter = new LgnnEventRouter();
