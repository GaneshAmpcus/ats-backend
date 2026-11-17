"""Rebuild the portable Postman collection using only the Python standard library."""
import json
from pathlib import Path

ROOT = Path(__file__).parent
SAMPLE = "Jane Doe\njane.doe@example.com\nPython Developer\nSkills: Python, FastAPI, PostgreSQL\nExperience: Software Engineer at Example Ltd, January 2022 - December 2024\nBuilt REST APIs.\nEducation: BSc Computer Science, Example University, 2021"


def event(code, kind="test"):
    return {"listen": kind, "script": {"type": "text/javascript", "exec": code.splitlines()}}


def request(name, method, path, status=200, body=None, ai=False, checks="", description="", auth=True):
    base = "{{ai_base_url}}{{ai_api_prefix}}" if ai else "{{core_base_url}}/api/v1"
    headers = [{"key": "X-API-Key", "value": "{{ai_service_api_key}}"}] if ai and auth else []
    req = {"method": method, "header": headers, "url": base + path, "description": description}
    if body:
        req["body"] = body
        if body["mode"] == "raw":
            headers.append({"key": "Content-Type", "value": "application/json"})
    code = f'pm.test("HTTP {status}", () => pm.response.to.have.status({status}));\n'
    code += 'const data = pm.response.json();\n' + checks
    return {"name": name, "request": req, "event": [event(code)]}


def raw(data):
    return {"mode": "raw", "raw": json.dumps(data, indent=2), "options": {"raw": {"language": "json"}}}


def upload(names, bulk=False, candidate=False):
    fields = [{"key": "files" if bulk else "file", "type": "file", "src": "fixtures/" + n} for n in names]
    if candidate:
        fields.append({"key": "candidate_id", "type": "text", "value": "{{candidate_id}}"})
    return {"mode": "formdata", "formdata": fields}


job_checks = '''pm.test("Valid job state", () => pm.expect(data.status).to.be.oneOf(["queued", "processing", "completed", "failed"]));
pm.test("Job has not failed", () => pm.expect(data.status, data.error_message || "").not.to.eql("failed"));
pm.test("Embedding has not failed", () => pm.expect(data.embedding_status, data.embedding_error || "").not.to.eql("failed"));
if (data.embedding_status === "completed") {
  pm.test("Embedding persistence confirmed", () => {
    pm.expect(data.embedding_count).to.be.a("number").and.above(0);
    pm.expect(data.embedding_error).to.eql(null);
    pm.expect(data.embedding_completed_at).to.be.a("string");
  });
}
if (data.status === "completed") {
  pm.test("Result persisted", () => {
    pm.expect(data.parsed_data).to.be.an("object");
    pm.expect(data.vector_chunks).to.be.an("array");
    pm.expect(data.error_message).to.eql(null);
    pm.expect(data.completed_at).to.be.a("string");
  });
}
'''


def poll_code(batch=False):
    terminal = ('data.jobs.every(j => j.status === "failed" || (j.status === "completed" && ["completed", "failed"].includes(j.embedding_status)))'
                if batch else '(data.status === "failed" || (data.status === "completed" && ["completed", "failed"].includes(data.embedding_status)))')
    key = "batch_poll_count" if batch else "job_poll_count"
    return f'''
if (pm.response.code === 200 && !({terminal})) {{
  if (String(pm.variables.get("auto_poll")) === "true") {{
    const count = Number(pm.collectionVariables.get("{key}") || 0) + 1;
    pm.collectionVariables.set("{key}", count);
    if (count < Number(pm.variables.get("max_poll_attempts"))) {{
      pm.execution.setNextRequest(pm.info.requestId);
    }} else {{
      pm.test("Polling finished before limit", () => {{ throw new Error("Still pending; inspect worker and resend GET later"); }});
      pm.collectionVariables.unset("{key}");
      pm.execution.setNextRequest(null);
    }}
  }} else {{ console.log("Pending: resend this GET or use Runner with auto_poll=true"); }}
}} else {{ pm.collectionVariables.unset("{key}"); }}
'''


single = request("01 Upload single resume", "POST", "/resumes/parse", 202,
                 upload(["jane-doe.txt"], candidate=True), checks=job_checks + '''
if (pm.response.code === 202) { pm.collectionVariables.set("job_id", data.id); pm.collectionVariables.unset("job_poll_count"); }
pm.test("Candidate linked", () => pm.expect(data.candidate_id).to.eql(pm.variables.get("candidate_id")));
''', description="Select a PDF, DOCX or TXT in Body > form-data > file. candidate_id is optional metadata; no applicant is created. Do not set multipart Content-Type manually.")
single["event"].insert(0, event('pm.collectionVariables.unset("job_id");', "prerequest"))
poll = request("02 Poll single job", "GET", "/resumes/jobs/{{job_id}}", checks=job_checks + poll_code(), description="Wait for BOTH status and embedding_status to complete. Runner: auto_poll=true, delay=2000ms. embedding_count counts persisted pgvector rows; vector_chunks contains original text chunks.")
batch_checks = '''pm.test("Batch counts consistent", () => pm.expect(data.queued + data.processing + data.completed + data.failed).to.eql(data.total));
pm.test("All accepted jobs returned", () => pm.expect(data.jobs).to.have.lengthOf(data.total));
pm.test("No accepted jobs failed", () => pm.expect(data.failed).to.eql(0));
pm.test("No embeddings failed", () => data.jobs.forEach(j => pm.expect(j.embedding_status, j.embedding_error || "").not.to.eql("failed")));
data.jobs.filter(j => j.embedding_status === "completed").forEach(j => {
  pm.test("Batch job has stored vectors: " + j.id, () => pm.expect(j.embedding_count).to.be.above(0));
});
'''
bulk = request("01 Upload bulk resumes", "POST", "/resumes/parse/bulk", 202,
               upload(["jane-doe.txt", "alex-smith.txt"], bulk=True), checks=batch_checks + '''
if (pm.response.code === 202) { pm.collectionVariables.set("batch_id", data.id); pm.collectionVariables.set("batch_job_id", data.jobs[0].id); pm.collectionVariables.unset("batch_poll_count"); }
pm.test("Two accepted, none rejected", () => { pm.expect(data.total).to.eql(2); pm.expect(data.rejected).to.have.lengthOf(0); });
''', description="Repeat the files key for each file. Bulk does not accept candidate_id. Fixture assertions expect exactly two files.")
bulk["event"].insert(0, event('pm.collectionVariables.unset("batch_id"); pm.collectionVariables.unset("batch_job_id");', "prerequest"))
batch_poll = request("02 Poll batch", "GET", "/resumes/batches/{{batch_id}}", checks=batch_checks + poll_code(True))
mixed = request("Bulk partial validation rejection", "POST", "/resumes/parse/bulk", 202,
                upload(["jane-doe.txt", "unsupported.csv"], bulk=True), checks='pm.test("One accepted, one rejected", () => { pm.expect(data.total).to.eql(1); pm.expect(data.rejected).to.have.lengthOf(1); });', description="Accepted job still runs. Rejected files are not jobs and do not contribute to failed count. Save response ID to poll separately.")
negative = [mixed]
for name, filename, status in [("Unsupported extension", "unsupported.csv", 415), ("PDF signature mismatch", "invalid.pdf", 415), ("Empty file", "empty.txt", 400)]:
    negative.append(request(name, "POST", "/resumes/parse", status, upload([filename])))
negative += [
    request("Embedding blank text", "POST", "/embeddings", 422, raw({"texts": [" "]}), ai=True),
    request("Embedding empty batch", "POST", "/embeddings", 422, raw({"texts": []}), ai=True),
    request("Embedding missing API key", "POST", "/embeddings", 401, raw({"texts": ["Python"]}), ai=True, auth=False),
    request("Bulk all rejected", "POST", "/resumes/parse/bulk", 400, upload(["unsupported.csv"], bulk=True)),
    request("Missing upload", "POST", "/resumes/parse", 422),
    request("Invalid job UUID", "GET", "/resumes/jobs/not-a-uuid", 422),
    request("Unknown job UUID", "GET", "/resumes/jobs/{{$guid}}", 404),
    request("Unknown batch UUID", "GET", "/resumes/batches/{{$guid}}", 404),
    request("AI missing API key", "POST", "/parse-resume", 401, raw({"text": SAMPLE}), ai=True, auth=False, description="Requires AI_SERVICE_API_KEY configured on server; otherwise middleware returns 503."),
    request("AI blank text", "POST", "/parse-resume", 422, raw({"text": "   "}), ai=True),
    request("AI missing text", "POST", "/parse-resume", 422, raw({"filename": "cv.txt"}), ai=True),
]
variables = {"core_base_url": "http://localhost:8000", "ai_base_url": "http://localhost:8001", "ai_api_prefix": "/api/v1", "ai_service_api_key": "", "candidate_id": "postman-candidate-001", "job_id": "", "batch_id": "", "batch_job_id": "", "auto_poll": "false", "max_poll_attempts": "240"}
collection = {
    "info": {"name": "ATS Resume Parsing - End-to-End", "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json", "description": "All mounted resume APIs plus AI diagnostics. See README.md. Select a folder to run; choose local fixture files and set the AI key locally. Runner polling requires auto_poll=true and 2000ms request delay. Live parsing calls the configured LLM and persists uploads/results."},
    "auth": {"type": "noauth"},
    "variable": [{"key": k, "value": v, "type": "string"} for k, v in variables.items()],
    "item": [
        {"name": "00 AI diagnostics", "item": [request("AI health", "GET", "/health", ai=True, checks='pm.test("Healthy", () => pm.expect(data.status).to.eql("ok"));', description="Checks HTTP service/key only; does not test database, queue, or provider."), request("LLM connectivity", "POST", "/llm-test", body=raw({"message": "Reply with OK"}), ai=True, checks='pm.test("Nonempty response", () => pm.expect(data.response).to.be.a("string").and.not.empty);'), request("Parse text directly", "POST", "/parse-resume", body=raw({"text": SAMPLE, "filename": "jane-doe.txt"}), ai=True, checks='pm.test("Structured resume", () => { pm.expect(data.personal_info).to.be.an("object"); ["skills", "experience", "education", "projects", "certifications"].forEach(k => pm.expect(data[k]).to.be.an("array")); });', description="Synchronous text-only parsing; no upload, Core job, database record or chunks.")]},
        {"name": "01 Single resume flow", "item": [single, poll]},
        {"name": "02 Bulk resume flow", "item": [bulk, batch_poll, request("03 Inspect first bulk job", "GET", "/resumes/jobs/{{batch_job_id}}", checks=job_checks)]},
        {"name": "03 Negative and partial acceptance tests", "item": negative},
    ],
}
ROOT.mkdir(exist_ok=True)
collection["item"][0]["item"].append(request(
    "Generate embeddings directly", "POST", "/embeddings", ai=True,
    body=raw({"texts": ["Skills: Python, FastAPI, PostgreSQL", "Experience: Built REST APIs"]}),
    checks='''pm.test("384 dimensional vectors", () => {
      pm.expect(data.model).to.eql("sentence-transformers/all-MiniLM-L6-v2");
      pm.expect(data.dimensions).to.eql(384);
      pm.expect(data.embeddings).to.have.lengthOf(2);
      data.embeddings.forEach(v => { pm.expect(v).to.have.lengthOf(384); v.forEach(x => pm.expect(Number.isFinite(x)).to.eql(true)); });
    });''',
    description="Internal authenticated model diagnostic. Returns vectors only; the Core background task stores vectors. First model load may download weights and take longer."))
(ROOT / "resume-parsing.postman_collection.json").write_text(json.dumps(collection, indent=2) + "\n", encoding="utf-8")
environment = {"name": "ATS Resume Parsing - Local", "_postman_variable_scope": "environment", "values": [{"key": k, "value": v, "enabled": True, "type": "secret" if k == "ai_service_api_key" else "default"} for k, v in variables.items() if k not in {"job_id", "batch_id", "batch_job_id"}]}
(ROOT / "resume-parsing.local.postman_environment.json").write_text(json.dumps(environment, indent=2) + "\n", encoding="utf-8")
(ROOT / "fixtures").mkdir(exist_ok=True)
for name, text in {"jane-doe.txt": SAMPLE, "alex-smith.txt": SAMPLE.replace("Jane Doe", "Alex Smith").replace("jane.doe", "alex.smith"), "empty.txt": "", "invalid.pdf": "This is deliberately not a PDF.", "unsupported.csv": "name,skill\nTest,Python\n"}.items():
    (ROOT / "fixtures" / name).write_text(text, encoding="utf-8")
print("Generated collection, environment and five synthetic fixtures.")
