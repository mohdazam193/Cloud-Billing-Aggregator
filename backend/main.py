from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import boto3
from azure.identity import ClientSecretCredential
from azure.mgmt.costmanagement import CostManagementClient
from datetime import datetime, timedelta

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="dev-secret")

templates = Jinja2Templates(directory="templates")

DEMO_USER = "Napster193"
DEMO_PASS = "ChangeMe123"

@app.get("/", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == DEMO_USER and password == DEMO_PASS:
        request.session["user"] = True
        return RedirectResponse("/credentials", status_code=302)
    return RedirectResponse("/", status_code=302)

@app.get("/credentials", response_class=HTMLResponse)
def credentials_page(request: Request):
    if not request.session.get("user"):
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse("credentials.html", {"request": request})

@app.post("/credentials")
def save_credentials(request: Request,
    aws_access_key: str = Form(...),
    aws_secret_key: str = Form(...),
    tenant_id: str = Form(...),
    client_id: str = Form(...),
    client_secret: str = Form(...),
    subscription_id: str = Form(...)
):
    request.session["aws"] = {
        "access_key": aws_access_key,
        "secret_key": aws_secret_key
    }
    request.session["azure"] = {
        "tenant_id": tenant_id,
        "client_id": client_id,
        "client_secret": client_secret,
        "subscription_id": subscription_id
    }
    return RedirectResponse("/dashboard", status_code=302)

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    if "aws" not in request.session or "azure" not in request.session:
        return RedirectResponse("/", status_code=302)

    end = datetime.utcnow().date()
    start = end - timedelta(days=30)

    aws = request.session["aws"]
    ce = boto3.client("ce",
        aws_access_key_id=aws["access_key"],
        aws_secret_access_key=aws["secret_key"],
        region_name="us-east-1"
    )
    aws_cost = ce.get_cost_and_usage(
        TimePeriod={"Start": str(start), "End": str(end)},
        Granularity="MONTHLY",
        Metrics=["UnblendedCost"]
    )["ResultsByTime"][0]["Total"]["UnblendedCost"]["Amount"]

    az = request.session["azure"]
    cred = ClientSecretCredential(
        tenant_id=az["tenant_id"],
        client_id=az["client_id"],
        client_secret=az["client_secret"]
    )
    cm = CostManagementClient(cred)
    scope = f"/subscriptions/{az['subscription_id']}"
    query = {
        "type": "ActualCost",
        "timeframe": "MonthToDate",
        "dataset": {"granularity": "None",
        "aggregation": {"totalCost": {"name": "Cost", "function": "Sum"}}}
    }
    az_cost = cm.query.usage(scope, query).rows[0][0]

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "aws": aws_cost,
        "azure": az_cost,
        "total": float(aws_cost) + float(az_cost)
    })

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=302)
