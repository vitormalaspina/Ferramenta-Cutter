import { useEffect, useRef } from 'react';
import { SSEEvent } from '../types';

export function useSSE(jobId: string | null, onEvent: (event: SSEEvent) => void) {
  // Store the callback in a ref to prevent recreating EventSource on every render
  const onEventRef = useRef(onEvent);
  onEventRef.current = onEvent;

  useEffect(() => {
    if (!jobId) return;

    const url = `/api/jobs/${jobId}/events`;
    const eventSource = new EventSource(url);

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as SSEEvent;
        onEventRef.current(data);
      } catch (err) {
        console.error('Failed to parse SSE event:', err);
      }
    };

    eventSource.onerror = (error) => {
      console.error('SSE connection error:', error);
    };

    return () => {
      eventSource.close();
    };
  }, [jobId]); // Only reconnect if jobId changes, NEVER on onEvent change
}
