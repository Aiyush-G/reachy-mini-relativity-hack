#!/usr/bin/env bash
# Smoke-test the two A100 services after `brev port-forward` (slides 21).
set -u

echo "== LLM (Nemotron) on :8010 =="
curl -s http://localhost:8010/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model":"nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
    "messages":[{"role":"user","content":"say hi in 8 words"}],
    "max_tokens":400
  }' | jq -r '.choices[0].message.content // .choices[0].message.reasoning // "NO RESPONSE"'

echo
echo "== TTS (Qwen3-TTS) on :8002 =="
curl -s -X POST http://localhost:8002/speak \
  -H "Content-Type: application/json" \
  -d '{"text":"Place a clean mug on the bench.",
       "style":"Calm, clear lab assistant"}' --output /tmp/tea_test.wav
bytes=$(wc -c < /tmp/tea_test.wav)
echo "wrote /tmp/tea_test.wav ($bytes bytes)"
if [ "$bytes" -lt 1024 ]; then
  echo "⚠️  <1KB — likely an error string, not a WAV:"; cat /tmp/tea_test.wav
else
  echo "✅ looks like audio — playing it"; afplay /tmp/tea_test.wav 2>/dev/null || open /tmp/tea_test.wav
fi
