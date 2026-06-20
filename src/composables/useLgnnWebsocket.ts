import { ref, onMounted, onUnmounted } from 'vue'
import { eventRouter } from '../shared/EventRouter.ts'

export function useLgnnWebsocket(
  wsUrl: string, 
  fetchGraphData: () => void,
  activeDragNode: () => boolean,
  activeResizeNode: () => boolean
) {
  const ws = ref<WebSocket | null>(null);
  let isConnecting = false;

  const connectWebSocket = () => {
    if (isConnecting || (ws.value && ws.value.readyState === WebSocket.OPEN)) return;
    isConnecting = true;
    
    const socket = new WebSocket(wsUrl);
    ws.value = socket;
    
    socket.onopen = () => {
      isConnecting = false;
    };

    socket.onmessage = (event) => {
      // Pass the raw event to the EventRouter
      // EventRouter will throttle fetchGraphData via its own listener
      eventRouter.ingest(event);
    };

    socket.onclose = () => {
      isConnecting = false;
      ws.value = null;
      setTimeout(connectWebSocket, 3000); // Auto-reconnect
    };
    
    socket.onerror = () => {
      socket.close();
    }
  };

  const sendJson = (data: any) => {
    if (ws.value && ws.value.readyState === WebSocket.OPEN) {
      ws.value.send(JSON.stringify(data));
    }
  };

  onMounted(() => {
    // Register the fetchGraphData callback with the EventRouter
    // We wrap it to respect the local UI state flags (drag/resize/hidden)
    const handleGraphUpdate = () => {
      if (!activeDragNode() && !activeResizeNode() && !document.hidden) {
        fetchGraphData();
      }
    };
    
    eventRouter.onGraphUpdate(handleGraphUpdate);
    connectWebSocket();
    
    // Cleanup
    onUnmounted(() => {
      eventRouter.offGraphUpdate(handleGraphUpdate);
      if (ws.value) {
        ws.value.onclose = null; // Prevent reconnect on explicit unmount
        ws.value.close();
        ws.value = null;
      }
    });
  });

  return {
    ws,
    sendJson
  }
}

