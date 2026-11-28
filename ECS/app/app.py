#!/usr/bin/env python3
"""Tiny in-memory ToDo application for the Amazon ECS hands-on."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from urllib.parse import urlparse

TASKS = [
    {"id": 1, "title": "Build the container image", "done": True},
    {"id": 2, "title": "Push the image to Amazon ECR", "done": False},
]
NEXT_ID = 3

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ECS ToDo</title>
<style>
:root{color-scheme:light;font-family:Inter,system-ui,sans-serif;background:#f3f6fb;color:#152238}
*{box-sizing:border-box}body{margin:0;min-height:100vh;display:grid;place-items:center;padding:24px}
main{width:min(620px,100%);background:white;padding:32px;border-radius:18px;box-shadow:0 18px 55px #14213d18}
.eyebrow{color:#536dfe;font-size:.78rem;font-weight:800;letter-spacing:.12em;text-transform:uppercase}
h1{margin:.35rem 0;font-size:2rem}.sub{color:#637087;margin:0 0 24px}
form{display:flex;gap:10px}input{min-width:0;flex:1;padding:13px;border:1px solid #d7deea;border-radius:10px;font:inherit}
button{border:0;border-radius:10px;padding:12px 16px;background:#536dfe;color:white;font-weight:700;cursor:pointer}
ul{list-style:none;padding:0;margin:22px 0 0}li{display:flex;align-items:center;gap:12px;padding:13px 0;border-bottom:1px solid #edf0f5}
li span{flex:1;overflow-wrap:anywhere}.done{text-decoration:line-through;color:#8b96a8}
.remove{background:#eef1f7;color:#3c4a60;padding:8px 11px}.footer{display:flex;justify-content:space-between;margin-top:22px;color:#778399;font-size:.82rem}
</style></head>
<body><main><div class="eyebrow">Amazon ECS · Fargate demo</div><h1>My ToDo List</h1>
<p class="sub">A tiny containerized app running as an ECS service.</p>
<form id="form"><input id="title" maxlength="100" placeholder="What needs to be done?" required><button>Add task</button></form>
<ul id="tasks"></ul><div class="footer"><span id="count">Loading…</span><span>Container port: 8080</span></div></main>
<script>
const list=document.querySelector('#tasks'),form=document.querySelector('#form'),input=document.querySelector('#title');
async function refresh(){const r=await fetch('/api/tasks');const tasks=await r.json();list.innerHTML='';
tasks.forEach(t=>{const li=document.createElement('li'),cb=document.createElement('input');cb.type='checkbox';cb.checked=t.done;cb.addEventListener('change',()=>update(t.id,{done:cb.checked}));const span=document.createElement('span');span.textContent=t.title;if(t.done)span.className='done';const del=document.createElement('button');del.textContent='Remove';del.className='remove';del.addEventListener('click',()=>removeTask(t.id));li.append(cb,span,del);list.append(li)});
document.querySelector('#count').textContent=tasks.filter(t=>!t.done).length+' open · '+tasks.length+' total'}
async function update(id,data){await fetch('/api/tasks/'+id,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});refresh()}
async function removeTask(id){await fetch('/api/tasks/'+id,{method:'DELETE'});refresh()}
form.addEventListener('submit',async e=>{e.preventDefault();const title=input.value.trim();if(!title)return;await fetch('/api/tasks',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({title})});input.value='';refresh()});
refresh();
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def send_json(self, data, status=200):
        payload = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        if self.path == "/healthz":
            return self.send_json({"status": "ok"})
        if self.path == "/api/tasks":
            return self.send_json(TASKS)
        if self.path == "/":
            body = PAGE.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            return self.wfile.write(body)
        self.send_json({"error": "not found"}, 404)

    def do_POST(self):
        global NEXT_ID
        if self.path != "/api/tasks":
            return self.send_json({"error": "not found"}, 404)
        try:
            data = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            title = str(data.get("title", "")).strip()
        except (ValueError, json.JSONDecodeError):
            return self.send_json({"error": "invalid JSON"}, 400)
        if not title or len(title) > 100:
            return self.send_json({"error": "title must be 1–100 characters"}, 400)
        task = {"id": NEXT_ID, "title": title, "done": False}
        NEXT_ID += 1
        TASKS.append(task)
        self.send_json(task, 201)

    def do_PATCH(self):
        try:
            task_id = int(urlparse(self.path).path.rsplit("/", 1)[-1])
            data = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        except (ValueError, json.JSONDecodeError):
            return self.send_json({"error": "invalid request"}, 400)
        task = next((t for t in TASKS if t["id"] == task_id), None)
        if task is None:
            return self.send_json({"error": "not found"}, 404)
        if "done" in data:
            task["done"] = bool(data["done"])
        self.send_json(task)

    def do_DELETE(self):
        try:
            task_id = int(urlparse(self.path).path.rsplit("/", 1)[-1])
        except ValueError:
            return self.send_json({"error": "invalid task id"}, 400)
        for index, task in enumerate(TASKS):
            if task["id"] == task_id:
                TASKS.pop(index)
                return self.send_json({"deleted": task_id})
        self.send_json({"error": "not found"}, 404)

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args), flush=True)


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
