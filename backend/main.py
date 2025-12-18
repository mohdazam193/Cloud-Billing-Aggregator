from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles
import boto3
from azure.identity import ClientSecretCredential
from azure.mgmt.costmanagement import CostManagementClient
from datetime import datetime, timedelta

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="dev-secret")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

USER="Napster193"
PASS="ChangeMe123"

@app.get("/", response_class=HTMLResponse)
def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def do_login(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == USER and password == PASS:
        request.session["user"] = True
        return RedirectResponse("/credentials", status_code=302)
    return RedirectResponse("/", status_code=302)

@app.get("/credentials", response_class=HTMLResponse)
def creds(request: Request):
    if "user" not in request.session:
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse("credentials.html", {"request": request})

@app.post("/credentials")
def save_creds(
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
    request.session.clear()
    request.session["user"] = True
    if use_aws:
        request.session["aws"]={"access_key":aws_access_key,"secret_key":aws_secret_key}
    if use_azure:
        request.session["azure"]={"tenant_id":tenant_id,"client_id":client_id,"client_secret":client_secret,"subscription_id":subscription_id}
    return RedirectResponse("/dashboard", status_code=302)

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    if "user" not in request.session:
        return RedirectResponse("/", status_code=302)

    days=int(request.query_params.get("days",30))
    end=datetime.utcnow().date()
    start=end-timedelta(days=days)

    aws_services=[]
    azure_services=[]
    aws_total=0
    azure_total=0

    if "aws" in request.session:
        aws=request.session["aws"]
        ce=boto3.client("ce",aws_access_key_id=aws["access_key"],aws_secret_access_key=aws["secret_key"],region_name="us-east-1")
        resp=ce.get_cost_and_usage(TimePeriod={"Start":str(start),"End":str(end)},Granularity="MONTHLY",Metrics=["UnblendedCost"],GroupBy=[{"Type":"DIMENSION","Key":"SERVICE"}])
        for g in resp["ResultsByTime"][0]["Groups"]:
            c=float(g["Metrics"]["UnblendedCost"]["Amount"])
            aws_services.append({"service":g["Keys"][0],"cost":c})
            aws_total+=c

    if "azure" in request.session:
        az=request.session["azure"]
        cred=ClientSecretCredential(tenant_id=az["tenant_id"],client_id=az["client_id"],client_secret=az["client_secret"])
        cm=CostManagementClient(cred)
        scope=f"/subscriptions/{az['subscription_id']}"
        q={"type":"ActualCost","timeframe":"Custom","timePeriod":{"from":start.isoformat(),"to":end.isoformat()},"dataset":{"granularity":"None","aggregation":{"totalCost":{"name":"Cost","function":"Sum"}},"grouping":[{"type":"Dimension","name":"ServiceName"}]}}
        res=cm.query.usage(scope,q)
        for r in res.rows:
            azure_services.append({"service":r[0],"cost":r[1]})
            azure_total+=r[1]

    return templates.TemplateResponse("dashboard.html",{"request":request,"days":days,"aws_total":aws_total,"azure_total":azure_total,"total":aws_total+azure_total,"aws_services":aws_services,"azure_services":azure_services})

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=302)
