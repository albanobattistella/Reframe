import urllib.request
import json
import subprocess

cmd = [
    "curl", "-s",
    "-F", "file=@test.mp4",
    "-F", "x=0", "-F", "y=0", "-F", "width=1280", "-F", "height=720",
    "-F", "quality=high", "-F", "muteAudio=false", "-F", "useGpu=false",
    "-F", "trimStart=0", "-F", "trimEnd=1",
    "-F", "subtitleEnabled=true",
    "-F", "subtitleModel=tiny",
    "-F", "subtitleFont=Arial",
    "-F", "subtitleColor=#ffffff",
    "-F", "subtitleHighlight=#ffff00",
    "-F", "subtitleStroke=#000000",
    "-F", "subtitleX=100", "-F", "subtitleY=100", "-F", "subtitleW=300", "-F", "subtitleH=100",
    "http://localhost:8080/api/process"
]
res = subprocess.run(cmd, capture_output=True, text=True)
print(res.stdout)
