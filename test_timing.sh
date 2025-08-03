#!/bin/bash

echo "🧪 Testing Slack command response timing"
echo ""

# Test data that mimics a Slack slash command
TEST_DATA="token=test_token&team_id=T098RS8BJ84&team_domain=test&channel_id=C099CAA08HW&channel_name=ai-assistant&user_id=U098RS8C39A&user_name=test_user&command=/ai&text=test&api_app_id=A099CEH0DB2&is_enterprise_install=false&response_url=https://hooks.slack.com/commands/test/response&trigger_id=test_trigger"

TIMESTAMP=$(date +%s)

echo "Testing production server timing..."
echo "Sending request to: https://decouple-ai.onrender.com/slack"
echo ""

# Test timing with curl
time_output=$(curl -w "@-" -o response.json -s \
  -X POST \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "X-Slack-Request-Timestamp: $TIMESTAMP" \
  -H "X-Slack-Signature: v0=test_signature" \
  -d "$TEST_DATA" \
  https://decouple-ai.onrender.com/slack <<'EOF'
{
  "time_namelookup": %{time_namelookup},
  "time_connect": %{time_connect},
  "time_appconnect": %{time_appconnect},
  "time_pretransfer": %{time_pretransfer},
  "time_redirect": %{time_redirect},
  "time_starttransfer": %{time_starttransfer},
  "time_total": %{time_total},
  "http_code": %{http_code},
  "size_download": %{size_download}
}
EOF
)

echo "Timing results:"
echo "$time_output" | jq '.'

echo ""
echo "Response body:"
cat response.json | jq '.'

echo ""
total_time=$(echo "$time_output" | jq -r '.time_total')
http_code=$(echo "$time_output" | jq -r '.http_code')

if (( $(echo "$total_time < 3.0" | bc -l) )); then
    echo "🎉 SUCCESS: Response time ($total_time s) is under 3 seconds!"
else
    echo "❌ TIMEOUT: Response took $total_time seconds (over 3s limit)"
fi

if [ "$http_code" = "200" ]; then
    echo "✅ HTTP Status: $http_code (OK)"
else
    echo "❌ HTTP Status: $http_code (Error)"
fi

echo ""
echo "📝 Notes:"
echo "- Slack requires responses within 3 seconds"
echo "- Times over 3s will show 'operation timed out' to users"
echo "- Current implementation may be doing API calls before responding"

# Cleanup
rm -f response.json
