import type { SSEEvent } from "@/lib/schemas";

/**
 * Parses a fetch Response's streaming body as Server-Sent Events.
 *
 * The browser's native EventSource can't be used here because it only
 * supports GET with no request body, and starting a research run needs a
 * POST body (the topic + provider config). This reads the same wire format
 * by hand instead.
 */
export async function* readSSE(response: Response): AsyncGenerator<SSEEvent> {
  if (!response.body) return;

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      // Normalize CRLF -> LF up front: sse-starlette emits "\r\n\r\n" event
      // separators, not "\n\n". Re-running this over the whole remaining
      // buffer each read is safe even if a "\r\n" is split across chunks.
      buffer = (buffer + decoder.decode(value, { stream: true })).replace(/\r\n/g, "\n");

      let sepIndex: number;
      while ((sepIndex = buffer.indexOf("\n\n")) !== -1) {
        const rawEvent = buffer.slice(0, sepIndex);
        buffer = buffer.slice(sepIndex + 2);
        const parsed = parseEventBlock(rawEvent);
        if (parsed) yield parsed;
      }
    }
  } finally {
    reader.releaseLock();
  }
}

function parseEventBlock(block: string): SSEEvent | null {
  let eventName = "message";
  const dataLines: string[] = [];

  for (const line of block.split("\n")) {
    if (line.startsWith("event:")) eventName = line.slice("event:".length).trim();
    else if (line.startsWith("data:")) dataLines.push(line.slice("data:".length).trim());
  }

  if (dataLines.length === 0) return null;

  try {
    const data = JSON.parse(dataLines.join(""));
    return { event: eventName, data } as SSEEvent;
  } catch {
    return null;
  }
}
