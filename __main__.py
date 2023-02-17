import hashlib

import pulumi_azure as azure_legacy
import pulumi_azure_native.dbforpostgresql as postgresql
import pulumi_azure_native.insights as insights
import pulumi_azure_native.resources as resource
import pulumi_azure_native.sql as sql
import pulumi_azure_native.storage as storage
import pulumi_azure_native.web as web
from pulumi import Config, Output, asset, export

config = Config()

username = "pulumi"
webapp_docker_url = "turingcropapp/webapp:dev"
ingressfunctions_docker_url = "turingcropapp/functions:dev"
modelfunctions_docker_url = "turingcropapp/modelfunctions:dev"
resource_name_prefix = "cropdev"
sql_server_user = "cropdbadmin"
sql_db_name = "app_db"
models_fileshare_name = "models-share"
ges_data_dir = "ges-data"
sql_server_password = config.require("sql-server-password")
default_user_password = config.require("default-user-password")
hyper_apikey = config.require("hyper-apikey")
openweathermap_apikey = config.require("openweathermap-apikey")
stark_password = config.require("stark-password")
stark_username = config.require("stark-username")
growapp_database = config.require("growapp-database")
growapp_ip = config.require("growapp-ip")
growapp_password = config.require("growapp-password")
growapp_schema = config.require("growapp-schema")
growapp_username = config.require("growapp-username")
postgres_allowed_ips = config.get("postgres-allowed-ips")

resource_group = resource.ResourceGroup(f"{resource_name_prefix}-rg")


def get_connection_string(account_name, resource_group_name):
    storage_account_keys = storage.list_storage_account_keys(
        account_name=account_name, resource_group_name=resource_group_name
    )
    primary_storage_key = storage_account_keys.keys[0].value
    connection_string = Output.format(
        "DefaultEndpointsProtocol=https;AccountName={0};AccountKey={1}",
        account_name,
        primary_storage_key,
    )
    return connection_string


sql_server_name = f"{resource_name_prefix}-postgresql"
sql_server = postgresql.Server(
    sql_server_name,
    server_name=sql_server_name,
    resource_group_name=resource_group.name,
    properties=postgresql.ServerPropertiesForDefaultCreateArgs(
        administrator_login=sql_server_user,
        administrator_login_password=sql_server_password,
        create_mode="Default",
        ssl_enforcement=postgresql.SslEnforcementEnum.DISABLED,
        minimal_tls_version=postgresql.MinimalTlsVersionEnum.TLS_ENFORCEMENT_DISABLED,
        storage_profile=postgresql.StorageProfileArgs(
            backup_retention_days=14,
            geo_redundant_backup="Disabled",
            storage_autogrow=postgresql.StorageAutogrow.ENABLED,
            storage_mb=5120,
        ),
    ),
    sku=postgresql.SkuArgs(
        capacity=2,
        family="Gen5",
        name="B_Gen5_2",
        tier="Basic",
    ),
)

sql_db = postgresql.Database(
    sql_db_name,
    charset="UTF8",
    collation="English_United States.1252",
    database_name=sql_db_name,
    resource_group_name=resource_group.name,
    server_name=sql_server.name,
)

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

# Storage accounts can't have special characters in their names, hence no hyphen for
# this one after the prefix.
storage_account = storage.StorageAccount(
    f"{resource_name_prefix}sa",
    resource_group_name=resource_group.name,
    sku=storage.SkuArgs(name="Standard_LRS"),
    kind=storage.Kind.STORAGE_V2,
)
sa_connection_string = get_connection_string(storage_account.name, resource_group.name)

webapp_settings = [
    web.NameValuePairArgs(
        name="APPINSIGHTS_INSTRUMENTATIONKEY", value=app_insights.instrumentation_key
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
    web.NameValuePairArgs(name="WEBSITES_ENABLE_APP_SERVICE_STORAGE", value="false"),
    web.NameValuePairArgs(
        name="DOCKER_REGISTRY_SERVER_URL", value="https://index.docker.io/v1"
    ),
    web.NameValuePairArgs(name="DOCKER_ENABLE_CI", value="true"),
    web.NameValuePairArgs(
        name="CROP_SQL_HOST", value=f"{sql_server_name}.postgres.database.azure.com"
    ),
    web.NameValuePairArgs(name="CROP_SQL_PASS", value=sql_server_password),
    web.NameValuePairArgs(name="CROP_SQL_PORT", value="5432"),
    web.NameValuePairArgs(
        name="CROP_SQL_USER", value=f"{sql_server_user}@{sql_server_name}"
    ),
    web.NameValuePairArgs(name="CROP_SQL_USERNAME", value=sql_server_user),
    web.NameValuePairArgs(name="CROP_SQL_DBNAME", value=sql_db_name),
    web.NameValuePairArgs(
        name="CROP_DEFAULT_USER_PASS", value=f"{default_user_password}"
    ),
]
webapp = web.WebApp(
    f"{resource_name_prefix}-webapp",
    resource_group_name=resource_group.name,
    server_farm_id=app_service_plan.id,
    site_config=web.SiteConfigArgs(
        app_settings=webapp_settings,
        always_on=True,
        linux_fx_version=f"DOCKER|{webapp_docker_url}",
    ),
    https_only=True,
)

ingress_fa_settings = [
    web.NameValuePairArgs(name="AzureWebJobsStorage", value=sa_connection_string),
    web.NameValuePairArgs(
        name="APPINSIGHTS_INSTRUMENTATIONKEY", value=app_insights.instrumentation_key
    ),
    web.NameValuePairArgs(
        name="APPLICATIONINSIGHTS_CONNECTION_STRING",
        value=app_insights.instrumentation_key.apply(
            lambda key: "InstrumentationKey=" + key
        ),
    ),
    web.NameValuePairArgs(name="FUNCTIONS_EXTENSION_VERSION", value="~3"),
    web.NameValuePairArgs(name="WEBSITES_ENABLE_APP_SERVICE_STORAGE", value="false"),
    web.NameValuePairArgs(
        name="DOCKER_REGISTRY_SERVER_URL", value="https://index.docker.io/v1"
    ),
    web.NameValuePairArgs(name="DOCKER_ENABLE_CI", value="true"),
    web.NameValuePairArgs(
        name="CROP_SQL_HOST", value=f"{sql_server_name}.postgres.database.azure.com"
    ),
    web.NameValuePairArgs(name="CROP_SQL_PASS", value=sql_server_password),
    web.NameValuePairArgs(name="CROP_SQL_PORT", value="5432"),
    web.NameValuePairArgs(
        name="CROP_SQL_USER", value=f"{sql_server_user}@{sql_server_name}"
    ),
    web.NameValuePairArgs(name="CROP_SQL_USERNAME", value=sql_server_user),
    web.NameValuePairArgs(name="CROP_SQL_DBNAME", value=sql_db_name),
    web.NameValuePairArgs(name="CROP_HYPER_APIKEY", value=hyper_apikey),
    web.NameValuePairArgs(
        name="CROP_OPENWEATHERMAP_APIKEY", value=openweathermap_apikey
    ),
    web.NameValuePairArgs(name="CROP_STARK_PASS", value=stark_password),
    web.NameValuePairArgs(name="CROP_STARK_USERNAME", value=stark_username),
    web.NameValuePairArgs(name="GROWAPP_DATABASE", value=growapp_database),
    web.NameValuePairArgs(name="GROWAPP_IP", value=growapp_ip),
    web.NameValuePairArgs(name="GROWAPP_PASS", value=growapp_password),
    web.NameValuePairArgs(name="GROWAPP_SCHEMA", value=growapp_schema),
    web.NameValuePairArgs(name="GROWAPP_USERNAME", value=growapp_username),
]
ingress_app = web.WebApp(
    f"{resource_name_prefix}-ingress-fa",
    resource_group_name=resource_group.name,
    kind="functionapp",
    server_farm_id=app_service_plan.id,
    site_config=web.SiteConfigArgs(
        app_settings=ingress_fa_settings,
        linux_fx_version=f"DOCKER|{ingressfunctions_docker_url}",
    ),
    https_only=True,
)

models_fa_fileshare = storage.FileShare(
    f"{resource_name_prefix}-models-share",
    account_name=storage_account.name,
    resource_group_name=resource_group.name,
    share_name=models_fileshare_name,
)

# Note that this uses an resource type from the old pulumi_azure package, rather than
# the new pulumi_azure_native, unlike all the other resources. The new package doesn't
# seem to (yet?) have equivalent functionality.
# TODO Is the file share even getting used by GES? There seems to be nothing there, but
# I don't know where GES is writing its files.
models_share_dir = azure_legacy.storage.ShareDirectory(
    f"{resource_name_prefix}-models-share-dir",
    share_name=models_fa_fileshare.name,
    storage_account_name=storage_account.name,
    name=ges_data_dir,
)


models_fa_settings = [
    web.NameValuePairArgs(name="AzureWebJobsStorage", value=sa_connection_string),
    web.NameValuePairArgs(
        name="APPINSIGHTS_INSTRUMENTATIONKEY", value=app_insights.instrumentation_key
    ),
    web.NameValuePairArgs(
        name="APPLICATIONINSIGHTS_CONNECTION_STRING",
        value=app_insights.instrumentation_key.apply(
            lambda key: "InstrumentationKey=" + key
        ),
    ),
    web.NameValuePairArgs(name="FUNCTIONS_EXTENSION_VERSION", value="~3"),
    web.NameValuePairArgs(name="WEBSITES_ENABLE_APP_SERVICE_STORAGE", value="false"),
    web.NameValuePairArgs(
        name="DOCKER_REGISTRY_SERVER_URL", value="https://index.docker.io/v1"
    ),
    web.NameValuePairArgs(name="DOCKER_ENABLE_CI", value="true"),
    web.NameValuePairArgs(
        name="CROP_SQL_HOST", value=f"{sql_server_name}.postgres.database.azure.com"
    ),
    web.NameValuePairArgs(name="CROP_SQL_PASS", value=sql_server_password),
    web.NameValuePairArgs(name="CROP_SQL_PORT", value="5432"),
    web.NameValuePairArgs(
        name="CROP_SQL_USER", value=f"{sql_server_user}@{sql_server_name}"
    ),
    web.NameValuePairArgs(name="CROP_SQL_USERNAME", value=sql_server_user),
    web.NameValuePairArgs(name="CROP_SQL_DBNAME", value=sql_db_name),
    web.NameValuePairArgs(name="CROP_DATA_DIR", value=f"/{ges_data_dir}"),
    # web.NameValuePairArgs(name="WEBSITE_CONTENTAZUREFILECONNECTIONSTRING", value=None),
    # web.NameValuePairArgs(name="WEBSITE_CONTENTSHARE", value=None),
]
models_app = web.WebApp(
    f"{resource_name_prefix}-models-fa",
    resource_group_name=resource_group.name,
    kind="functionapp",
    server_farm_id=app_service_plan.id,
    site_config=web.SiteConfigArgs(
        app_settings=models_fa_settings,
        linux_fx_version=f"DOCKER|{modelfunctions_docker_url}",
        azure_storage_accounts=web.AzureStorageInfoValueArgs(
            account_name=storage_account.name,
            share_name=models_fa_fileshare.name,
            mount_path=models_share_dir.name,
            type=web.AzureStorageType.AZURE_FILES,
        ),
    ),
    https_only=True,
)


firewall_ips = []


def create_postgres_firewall_rules(ips_string, num_hash_chars=4):
    """Given a list of comma separated IP addresses, create a firewall rule for the
    Postgres server to allow each one of them.

    We append a part of the IPs hash to the name, to create a unique name for the role.
    We use the hash rather than the actual IP to not reveal actual IPs in the resource
    names.
    """
    global firewall_ips
    rules = []
    for ip in ips_string.split(","):
        if ip in firewall_ips:
            # Don't try to create another rule for this same IP, if it comes up again.
            continue
        h = hashlib.sha256(bytes(ip, encoding="utf8")).hexdigest()[:num_hash_chars]
        rules.append(
            postgresql.FirewallRule(
                f"{resource_name_prefix}-fwr{h}",
                resource_group_name=resource_group.name,
                start_ip_address=ip,
                end_ip_address=ip,
                server_name=sql_server.name,
            )
        )
        firewall_ips.append(ip)
    return rules


# Using apply in this way explicitly breaks the Pulumi docs' warning that one shouldn't
# create new resources within apply. However, this is also how some officially Pulumi
# examples do it, and I don't there's another way. (Ideally we would need a function
# from Option[list] to list[Option].) I think this might mean that `pulumi preview`
# doesn't work correctly though, it might not show the firewall rules.
webapp.outbound_ip_addresses.apply(create_postgres_firewall_rules)
ingress_app.outbound_ip_addresses.apply(create_postgres_firewall_rules)
if postgres_allowed_ips is not None:
    create_postgres_firewall_rules(postgres_allowed_ips)

export(
    "endpoint", webapp.default_host_name.apply(lambda endpoint: "https://" + endpoint)
)
