import pulumi_azure_native.insights as insights
import pulumi_azure_native.resources as resource
import pulumi_azure_native.sql as sql
import pulumi_azure_native.storage as storage
import pulumi_azure_native.web as web
from pulumi import Config, Output, asset, export
from pulumi_azure_native.storage import BlobContainer, PublicAccess, StorageAccount

username = "pulumi"
webapp_docker_url = "turingcropapp/webapp:dev"

config = Config()
pwd = config.require("sql-server-password")

resource_group = resource.ResourceGroup("crop-dev-rg")

app_service_plan = web.AppServicePlan(
    "crop-dev-web-asp",
    resource_group_name=resource_group.name,
    kind="Linux",
    reserved=True,
    sku=web.SkuDescriptionArgs(
        tier="Premium",
        name="P1v2",
    ),
)

app_insights = insights.Component(
    "crop-dev-web-ai",
    application_type=insights.ApplicationType.WEB,
    kind="web",
    resource_group_name=resource_group.name,
)

sql_server = sql.Server(
    "crop-dev-sql-server",
    resource_group_name=resource_group.name,
    administrator_login=username,
    administrator_login_password=pwd,
    version="12.0",
)

database = sql.Database(
    "crop-dev-sql-db",
    resource_group_name=resource_group.name,
    server_name=sql_server.name,
    sku=sql.SkuArgs(
        name="S0",
    ),
)

connection_string = Output.concat(
    "Server=tcp:",
    sql_server.name,
    ".database.windows.net;initial ",
    "catalog=",
    database.name,
    ";user ID=",
    username,
    ";password=",
    pwd,
    ";Min Pool Size=0;Max Pool Size=30;Persist Security Info=true;",
)

app = web.WebApp(
    "crop-dev-web-as",
    resource_group_name=resource_group.name,
    server_farm_id=app_service_plan.id,
    site_config=web.SiteConfigArgs(
        app_settings=[
            web.NameValuePairArgs(
                name="APPINSIGHTS_INSTRUMENTATIONKEY",
                value=app_insights.instrumentation_key,
            ),
            web.NameValuePairArgs(
                name="APPLICATIONINSIGHTS_CONNECTION_STRING",
                value=app_insights.instrumentation_key.apply(
                    lambda key: "InstrumentationKey=" + key
                ),
            ),
            web.NameValuePairArgs(
                name="ApplicationInsightsAgent_EXTENSION_VERSION", value="~2"
            ),
            web.NameValuePairArgs(
                name="WEBSITES_ENABLE_APP_SERVICE_STORAGE",
                value="false",
            ),
        ],
        connection_strings=[
            web.ConnStringInfoArgs(
                name="db",
                type="SQLAzure",
                connection_string=connection_string,
            )
        ],
        always_on=True,
        linux_fx_version=f"DOCKER|{webapp_docker_url}",
    ),
    https_only=True,
)

export("endpoint", app.default_host_name.apply(lambda endpoint: "https://" + endpoint))
