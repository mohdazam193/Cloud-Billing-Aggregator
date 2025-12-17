from fastapi import FastAPI, Request, HTTPException, Query
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import JSONResponse
from datetime import datetime, timedelta
import boto3
from azure.identity import ClientSecretCredential
from azure.mgmt.costmanagement import CostManagementClient

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="dev-secret")

DEMO_USER = "Napster193"
DEMO_PASS = "ChangeMe123"

@app.post("/api/auth/login")
async def login(request: Request, payload: dict):
    if payload.get("username") == DEMO_USER and payload.get("password") == DEMO_PASS:
        request.session["user"] = True
        return {"status": "ok"}
    return JSONResponse(status_code=401, content={"error": "invalid login"})

@app.post("/api/auth/logout")
async def logout(request: Request):
    request.session.clear()
    return {"status": "logged out"}

@app.post("/api/cloud/login")
async def cloud_login(request: Request, payload: dict):
    if "user" not in request.session:
        raise HTTPException(status_code=401)
    request.session["aws"] = payload["aws"]
    request.session["azure"] = payload["azure"]
    return {"status": "connected"}

def date_range(days):
    end = datetime.utcnow().date()
    start = end - timedelta(days=days)
    return str(start), str(end)

@app.get("/api/summary")
def summary(request: Request, days: int = Query(30)):
    if "aws" not in request.session or "azure" not in request.session:
        raise HTTPException(status_code=401)

    start, end = date_range(days)

    aws = request.session["aws"]
    ce = boto3.client("ce",
        aws_access_key_id=aws["access_key"],
        aws_secret_access_key=aws["secret_key"],
        region_name="us-east-1"
    )

    aws_resp = ce.get_cost_and_usage(
        TimePeriod={"Start": start, "End": end},
        Granularity="DAILY",
        Metrics=["UnblendedCost"]
    )

    aws_total = sum(float(d["Total"]["UnblendedCost"]["Amount"]) for d in aws_resp["ResultsByTime"])

    az = request.session["azure"]
    cred = ClientSecretCredential(
        tenant_id=az["tenant_id"],
        client_id=az["client_id"],
        client_secret=az["client_secret"]
    )
    cm = CostManagementClient(cred)
    scope = f"/subscriptions/{az['subscription_id']}"

    az_query = {
        "type": "ActualCost",
        "timeframe": "Custom",
        "timePeriod": {"from": start, "to": end},
        "dataset": {
            "granularity": "Daily",
            "aggregation": {"totalCost": {"name": "Cost", "function": "Sum"}}
        }
    }

    az_resp = cm.query.usage(scope, az_query)
    az_total = sum(r[0] for r in az_resp.rows)

    return {
        "total": round(aws_total + az_total, 2),
        "aws": round(aws_total, 2),
        "azure": round(az_total, 2)
    }
