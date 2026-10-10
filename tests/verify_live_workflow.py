import urllib.request
import json

print("Testing End-to-End Workflow on Live Server: http://127.0.0.1:5000")

# 1. Initialize
req1 = urllib.request.Request("http://127.0.0.1:5000/api/interview/init", method="POST")
data1 = json.loads(urllib.request.urlopen(req1).read())
code = data1["session_code"]
print(f"Step 0/1 [Init]: Session={code}, Status={data1['status']}")
print(f"         Prompt: \"{data1['jarvis_voice_prompt']}\"")

# 2. Upload resume
boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
body_parts = [
    f"--{boundary}",
    'Content-Disposition: form-data; name="session_code"',
    '',
    code,
    f"--{boundary}",
    'Content-Disposition: form-data; name="resume"; filename="john_doe_resume.pdf"',
    'Content-Type: application/pdf',
    '',
    'Candidate Skills: Python, Flask, MySQL, Docker, REST API, Microservices',
    f"--{boundary}--",
    ''
]
body = "\r\n".join(body_parts).encode("utf-8")

req2 = urllib.request.Request("http://127.0.0.1:5000/api/interview/upload-resume", data=body, method="POST")
req2.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
data2 = json.loads(urllib.request.urlopen(req2).read())
print(f"Step 1   [Resume Uploaded]: Status={data2['status']}, Extracted Skills={data2['extracted_skills']}")
print(f"         Prompt: \"{data2['jarvis_voice_prompt']}\"")

# 3. Select Role
role_body = json.dumps({"session_code": code, "target_role": "Python Developer"}).encode("utf-8")
req3 = urllib.request.Request("http://127.0.0.1:5000/api/interview/select-role", data=role_body, method="POST")
req3.add_header("Content-Type", "application/json")
data3 = json.loads(urllib.request.urlopen(req3).read())
print(f"Step 2/3 [Role & Analysis]: Status={data3['status']}, Target Role={data3['target_role']}")

# 4. Ready For JARVIS Round Confirmation
print(f"Step 4   [Ready Screen]: Notification=\"{data3['notification']}\"")
action_btn_safe = data3['action_button'].encode('ascii', 'backslashreplace').decode('ascii')
print(f"         Prompt=\"{data3['prompt_question']}\", Action=\"{action_btn_safe}\"")

# 5. Continue Clicked -> Start Round
start_body = json.dumps({"session_code": code}).encode("utf-8")
req4 = urllib.request.Request("http://127.0.0.1:5000/api/interview/start-round", data=start_body, method="POST")
req4.add_header("Content-Type", "application/json")
data4 = json.loads(urllib.request.urlopen(req4).read())
print(f"Step 5   [Continue Clicked]: Popup=\"{data4['popup_message']}\", Voice=\"{data4['jarvis_voice_prompt']}\"")
print(f"         Question 1: [{data4['first_question']['question_code']}] {data4['first_question']['question_text']}")
print("\n>>> LIVE WORKFLOW TEST PASSED 100% SUCCESSFULLY! <<<")
