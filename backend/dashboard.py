from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from memory import get_call_stats
import uvicorn

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    stats = get_call_stats()

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Kisan Sakhi - Call Analytics</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background: #f0f7f0;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
            }}
            .container {{
                background: white;
                padding: 40px;
                border-radius: 16px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                text-align: center;
            }}
            h1 {{
                color: #2E7D32;
                margin-bottom: 30px;
            }}
            .stats {{
                display: flex;
                gap: 30px;
                justify-content: center;
            }}
            .card {{
                background: #E8F5E9;
                padding: 25px 35px;
                border-radius: 12px;
                min-width: 140px;
            }}
            .number {{
                font-size: 42px;
                font-weight: bold;
                color: #1B5E20;
            }}
            .label {{
                margin-top: 8px;
                color: #555;
                font-size: 16px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Kisan Sakhi – Call Analytics</h1>
            <div class="stats">
                <div class="card">
                    <div class="number">{stats['total']}</div>
                    <div class="label">Total Calls</div>
                </div>
                <div class="card">
                    <div class="number">{stats['successful']}</div>
                    <div class="label">Successful</div>
                </div>
                <div class="card">
                    <div class="number">{stats['failed']}</div>
                    <div class="label">Failed</div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return html

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)