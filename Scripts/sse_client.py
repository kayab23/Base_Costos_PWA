import sys
import httpx

def main():
    url = 'http://127.0.0.1:8000/autorizaciones/events'
    try:
        with httpx.Client(timeout=None) as client:
            with client.stream('GET', url) as resp:
                for raw in resp.iter_bytes():
                    try:
                        line = raw.decode('utf-8')
                    except Exception:
                        line = str(raw)
                    # SSE messages come as 'data: {...}\n\n'
                    if line.startswith('data: '):
                        payload = line[len('data: '):].strip()
                        print(payload)
                        sys.stdout.flush()
    except Exception as e:
        print('SSE client error:', e)

if __name__ == '__main__':
    main()
