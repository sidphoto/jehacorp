import { send } from '@vercel/queue';

export default async function handler(request, response) {
  if (request.method !== 'POST') return response.status(405).send('Method Not Allowed');
  const supplied = request.headers['x-queue-dispatch-secret'];
  if (!supplied || supplied !== process.env.JOB_PAYLOAD_SECRET) {
    return response.status(404).send('Not Found');
  }
  const idempotencyKey = request.headers['x-queue-idempotency-key'];
  const result = await send('jehacorp-jobs', request.body, {
    idempotencyKey,
    retentionSeconds: 86400,
  });
  return response.status(201).json(result);
}
