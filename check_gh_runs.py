import urllib.request, json
url = 'https://api.github.com/repos/ravindrareddy17/ai-video-generator/actions/runs?per_page=5'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
data = json.loads(urllib.request.urlopen(req).read())
for r in data['workflow_runs']:
    print(f"Run #{r['run_number']} | Status: {r['status']} | Conclusion: {r['conclusion']} | Date: {r['created_at']}")
