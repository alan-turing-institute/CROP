import pulumi_azure_native.dbforpostgresql as dbforpostgresql
import pulumi_azure_native.insights as insights
import pulumi_azure_native.resources as resource
import pulumi_azure_native.sql as sql
import pulumi_azure_native.storage as storage
import pulumi_azure_native.web as web
from pulumi import Config, Output, asset, export
from pulumi_azure_native.storage import BlobContainer, PublicAccess, StorageAccount

config = Config()

username = "pulumi"
webapp_docker_url = "turingcropapp/webapp:dev"
resource_name_prefix = "crop-dev"
sql_server_user = "cropdbadmin"
sql_server_password = config.require("sql-server-password")
sql_db_name = "app_db"

resource_group = resource.ResourceGroup(f"{resource_name_prefix}-rg")

app_service_plan = web.AppServicePlan(
    f"{resource_name_prefix}-web-asp",
    resource_group_name=resource_group.name,
    kind="Linux",
    reserved=True,
    sku=web.SkuDescriptionArgs(
        tier="Premium",
        name="P1v2",
    ),
)

app_insights = insights.Component(
    f"{resource_name_prefix}-web-ai",
    application_type=insights.ApplicationType.WEB,
    kind="web",
    resource_group_name=resource_group.name,
)

sql_server_name = f"{resource_name_prefix}-postgresql"
sql_server = dbforpostgresql.Server(
    sql_server_name,
    server_name=sql_server_name,
    resource_group_name=resource_group.name,
    properties=dbforpostgresql.ServerPropertiesForDefaultCreateArgs(
        administrator_login=sql_server_user,
        administrator_login_password=sql_server_password,
        create_mode="Default",
        minimal_tls_version="TLS1_2",
        ssl_enforcement=dbforpostgresql.SslEnforcementEnum.ENABLED,
        storage_profile=dbforpostgresql.StorageProfileArgs(
            backup_retention_days=14,
            geo_redundant_backup="Disabled",
            storage_autogrow=dbforpostgresql.StorageAutogrow.ENABLED,
            storage_mb=5120,
        ),
    ),
    sku=dbforpostgresql.SkuArgs(
        capacity=2,
        family="Gen5",
        name="B_Gen5_2",
        tier="Basic",
    ),
)

sql_db = dbforpostgresql.Database(
    sql_db_name,
    charset="UTF8",
    collation="English_United States.1252",
    database_name=sql_db_name,
    resource_group_name=resource_group.name,
    server_name=sql_server.name,
)


app = web.WebApp(
    f"{resource_name_prefix}-webapp",
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
            web.NameValuePairArgs(
                name="DOCKER_REGISTRY_SERVER_URL", value="https://index.docker.io/v1"
            ),
            web.NameValuePairArgs(
                name="CROP_SQL_HOST",
                value=f"{sql_server_name}.postgres.database.azure.com",
            ),
            web.NameValuePairArgs(name="CROP_SQL_PASS", value=sql_server_password),
            web.NameValuePairArgs(name="CROP_SQL_PORT", value="5432"),
            web.NameValuePairArgs(
                name="CROP_SQL_USER",
                value=f"{sql_server_user}@{sql_server_name}",
            ),
            web.NameValuePairArgs(name="CROP_SQL_USERNAME", value=sql_server_user),
            web.NameValuePairArgs(name="CROP_SQL_DBNAME", value=sql_db_name),
        ],
        always_on=True,
        linux_fx_version=f"DOCKER|{webapp_docker_url}",
    ),
    https_only=True,
)

export("endpoint", app.default_host_name.apply(lambda endpoint: "https://" + endpoint))
