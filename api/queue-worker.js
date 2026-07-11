import { handleCallback } from '@vercel/queue';

export default handleCallback(async (message) => {
  const host = process.env.VERCEL_URL || process.env.VERCEL_PROJECT_PRODUCTION_URL;
  if (!host) throw new Error('VERCEL_URL is unavailable');
  const response = await fetch(`https://${host}/api/worker`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(message),
  });
  if (!response.ok) {
    throw new Error(`Python worker failed: ${response.status} ${await response.text()}`);
  }
}, {
  visibilityTimeoutSeconds: 900,
  retry: (_error, metadata) => metadata.deliveryCount > 3
    ? { acknowledge: true }
    : { afterSeconds: Math.min(300, 15 * (2 ** metadata.deliveryCount)) },
});
