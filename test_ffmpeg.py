import asyncio
import re

async def run():
    cmd = [
        "ffmpeg", "-y", "-i", "media/uploads/4866e98b-5603-4d7c-83eb-ddb06ab43919_in.mp4",
        "-i", "media/uploads/4866e98b-5603-4d7c-83eb-ddb06ab43919_logo.png",
        "-filter_complex", 
        "[0:v]crop=300:300:0:0[bg]; [1:v]scale=150:-1[l_scaled]; [l_scaled]rotate=45*PI/180:c=none:ow=rotw(a):oh=roth(a)[l_rotated]; [bg][l_rotated]overlay=10:10[outv]",
        "-map", "[outv]", "-map", "0:a?",
        "-c:v", "libx264", "-c:a", "copy",
        "test_out.mp4"
    ]
    
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    stdout, stderr = await process.communicate()
    print("RETURN CODE:", process.returncode)
    print("STDERR:")
    print(stderr.decode()[-1000:])

asyncio.run(run())
