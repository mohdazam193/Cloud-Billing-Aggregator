from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from datetime import date, timedelta, datetime
import boto3, csv, io

from azure.identity import ClientSecretCredential
from azure.mgmt.costmanagement import CostManagementClient

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="dev-secret")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

ADMIN_USER = "Napster193"
ADMIN_PASS = "ChangeMe123"


def trend(curr, prev):
    if prev == 0:
        return 0, "neutral"
    pct = round(((curr - prev) / prev) * 100, 1)
    return pct, "up" if pct > 0 else "down"


@app.get("/", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USER and password == ADMIN_PASS:
        request.session.clear()
        request.session["user"] = True
        return RedirectResponse("/connect", status_code=302)
    return RedirectResponse("/", status_code=302)


@app.get("/connect", response_class=HTMLResponse)
def connect_page(request: Request):
    if not request.session.get("user"):
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse("connect.html", {"request": request})


@app.post("/connect")
def save_credentials(
    request: Request,
    use_aws: str = Form(None),
    use_azure: str = Form(None),
    aws_access_key: str = Form(None),
    aws_secret_key: str = Form(None),
    tenant_id: str = Form(None),
    client_id: str = Form(None),
    client_secret: str = Form(None),
    subscription_id: str = Form(None),
):
    request.session["aws"] = None
    request.session["azure"] = None

    if use_aws:
        request.session["aws"] = {
            "access_key": aws_access_key,
            "secret_key": aws_secret_key,
        }

    if use_azure:
        request.session["azure"] = {
            "tenant_id": tenant_id,
            "client_id": client_id,
            "client_secret": client_secret,
            "subscription_id": subscription_id,
        }

    return RedirectResponse("/dashboard", status_code=302)


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(
    request: Request,
    range: str = "30d",
    start_date: str | None = None,
    end_date: str | None = None,
):
    if not request.session.get("user"):
        return RedirectResponse("/", status_code=302)

    today = date.today()

    if range == "1d":
        start = today - timedelta(days=1)
        end = today
    elif range == "60d":
        start = today - timedelta(days=60)
        end = today
    elif range == "90d":
        start = today - timedelta(days=90)
        end = today
    elif range == "custom" and start_date and end_date:
        start = datetime.fromisoformat(start_date).date()
        end = datetime.fromisoformat(end_date).date()
    else:
        start = today - timedelta(days=30)
        end = today

    period_days = (end - start).days
    prev_start = start - timedelta(days=period_days)
    prev_end = start

    aws_total = azure_total = 0
    aws_prev = azure_prev = 0
    aws_services = []
    azure_services = []

    # ---------- AWS ----------
    if request.session.get("aws"):
        aws = request.session["aws"]
        ce = boto3.client(
            "ce",
            aws_access_key_id=aws["access_key"],
            aws_secret_access_key=aws["secret_key"],
            region_name="us-east-1",
        )

        curr = ce.get_cost_and_usage(
            TimePeriod={"Start": str(start), "End": str(end)},
            Granularity="MONTHLY",
            Metrics=["UnblendedCost"],
            GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
        )

        for g in curr["ResultsByTime"][0]["Groups"]:
            cost = float(g["Metrics"]["UnblendedCost"]["Amount"])
            aws_services.append({"service": g["Keys"][0], "cost": cost})
            aws_total += cost

        prev = ce.get_cost_and_usage(
            TimePeriod={"Start": str(prev_start), "End": str(prev_end)},
            Granularity="MONTHLY",
            Metrics=["UnblendedCost"],
        )
        aws_prev = float(prev["ResultsByTime"][0]["Total"]["UnblendedCost"]["Amount"])

    # ---------- Azure ----------
    if request.session.get("azure"):
        az = request.session["azure"]
        cred = ClientSecretCredential(
            tenant_id=az["tenant_id"],
            client_id=az["client_id"],
            client_secret=az["client_secret"],
        )
        cm = CostManagementClient(cred)
        scope = f"/subscriptions/{az['subscription_id']}"

        query = {
            "type": "ActualCost",
            "timeframe": "Custom",
            "timePeriod": {"from": start.isoformat(), "to": end.isoformat()},
            "dataset": {
                "granularity": "None",
                "aggregation": {"totalCost": {"name": "Cost", "function": "Sum"}},
                "grouping": [{"type": "Dimension", "name": "ServiceName"}],
            },
        }

        res = cm.query.usage(scope, query)
        for r in res.rows:
            azure_services.append({"service": r[0], "cost": r[1]})
            azure_total += r[1]

        prev_q = query.copy()
        prev_q["timePeriod"] = {
            "from": prev_start.isoformat(),
            "to": prev_end.isoformat(),
        }
        prev_res = cm.query.usage(scope, prev_q)
        azure_prev = sum(r[1] for r in prev_res.rows)

    aws_change, aws_trend = trend(aws_total, aws_prev)
    azure_change, azure_trend = trend(azure_total, azure_prev)

    request.session["aws_services"] = aws_services
    request.session["azure_services"] = azure_services

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "range": range,
            "total": aws_total + azure_total,
            "aws_total": aws_total,
            "azure_total": azure_total,
            "aws_services": aws_services,
            "azure_services": azure_services,
            "aws_change": aws_change,
            "azure_change": azure_change,
            "aws_trend": aws_trend,
            "azure_trend": azure_trend,
        },
    )


@app.get("/export/csv")
def export_csv(request: Request):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Cloud", "Service", "Cost (USD)"])

    for s in request.session.get("aws_services", []):
        writer.writerow(["AWS", s["service"], s["cost"]])

    for s in request.session.get("azure_services", []):
        writer.writerow(["Azure", s["service"], s["cost"]])

    output.seek(0)
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=cost-report.csv"},
    )


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=302)
