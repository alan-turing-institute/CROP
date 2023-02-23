"""The main Pulumi deployment script."""
import hashlib

import pulumi_azure as azure_legacy
import pulumi_azure_native.dbforpostgresql as postgresql
import pulumi_azure_native.insights as insights
import pulumi_azure_native.resources as resource
import pulumi_azure_native.sql as sql
import pulumi_azure_native.storage as storage
import pulumi_azure_native.web as web
from pulumi import Config, Output, export

CONFIG = Config()

USERNAME = "pulumi"
WEBAPP_DOCKER_URL = "turingcropapp/webapp:dev"
INGRESSFUNCTIONS_DOCKER_URL = "turingcropapp/functions:dev"
MODELFUNCTIONS_DOCKER_URL = "turingcropapp/modelfunctions:dev"
RESOURCE_NAME_PREFIX = "cropdev"
SQL_SERVER_USER = "cropdbadmin"
SQL_DB_NAME = "app_db"
MODELS_FILESHARE_NAME = "models-share"
GES_DATA_DIR = "ges-data"
SQL_SERVER_PASSWORD = CONFIG.require("sql-server-password")
DEFAULT_USER_PASSWORD = CONFIG.require("default-user-password")
HYPER_APIKEY = CONFIG.require("hyper-apikey")
OPENWEATHERMAP_APIKEY = CONFIG.require("openweathermap-apikey")
STARK_PASSWORD = CONFIG.require("stark-password")
STARK_USERNAME = CONFIG.require("stark-username")
GROWAPP_DATABASE = CONFIG.require("growapp-database")
GROWAPP_IP = CONFIG.require("growapp-ip")
GROWAPP_PASSWORD = CONFIG.require("growapp-password")
GROWAPP_SCHEMA = CONFIG.require("growapp-schema")
GROWAPP_USERNAME = CONFIG.require("growapp-username")
POSTGRES_ALLOWED_IPS = CONFIG.get("postgres-allowed-ips")


def get_connection_string(account_name, resource_group_name):
    storage_account_keys = storage.list_storage_account_keys_output(
        account_name=account_name, resource_group_name=resource_group_name
    )
    primary_storage_key = storage_account_keys.keys[0].value
    connection_string = Output.format(
        "DefaultEndpointsProtocol=https;AccountName={0};AccountKey={1}",
        account_name,
        primary_storage_key,
    )
    return connection_string


def create_sql_server(resource_group):
    sql_server_name = f"{RESOURCE_NAME_PREFIX}-postgresql"
    sql_server = postgresql.Server(
        sql_server_name,
        server_name=sql_server_name,
        resource_group_name=resource_group.name,
        properties=postgresql.ServerPropertiesForDefaultCreateArgs(
            administrator_login=SQL_SERVER_USER,
            administrator_login_password=SQL_SERVER_PASSWORD,
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
            capacity=2, family="Gen5", name="B_Gen5_2", tier="Basic"
        ),
    )
    return sql_server


def create_pg_database(resource_group, sql_server):
    pg_database = postgresql.Database(
        SQL_DB_NAME,
        charset="UTF8",
        collation="English_United States.1252",
        database_name=SQL_DB_NAME,
        resource_group_name=resource_group.name,
        server_name=sql_server.name,
    )
    return pg_database


def create_app_service_plan(resource_group):
    app_service_plan = web.AppServicePlan(
        f"{RESOURCE_NAME_PREFIX}-web-asp",
        resource_group_name=resource_group.name,
        kind="Linux",
        reserved=True,
        sku=web.SkuDescriptionArgs(tier="Premium", name="P1v2"),
    )
    return app_service_plan


def create_app_insights(resource_group):
    app_insights = insights.Component(
        f"{RESOURCE_NAME_PREFIX}-web-ai",
        application_type=insights.ApplicationType.WEB,
        kind="web",
        resource_group_name=resource_group.name,
    )
    return app_insights


def create_storage_account(resource_group):
    # Storage accounts can't have special characters in their names, hence no hyphen for
    # this one after the prefix.
    storage_account = storage.StorageAccount(
        f"{RESOURCE_NAME_PREFIX}sa",
        resource_group_name=resource_group.name,
        sku=storage.SkuArgs(name="Standard_LRS"),
        kind=storage.Kind.STORAGE_V2,
    )
    return storage_account


def create_webapp(resource_group, app_service_plan, sql_server, app_insights):
    crop_sql_host = Output.format("{0}.postgres.database.azure.com", sql_server.name)
    crop_sql_user = Output.format(f"{SQL_SERVER_USER}@{0}", sql_server.name)
    webapp_settings = [
        web.NameValuePairArgs(name=name, value=value)
        for name, value in (
            ("APPINSIGHTS_INSTRUMENTATIONKEY", app_insights.instrumentation_key),
            "APPLICATIONINSIGHTS_CONNECTION_STRING",
            app_insights.instrumentation_key.apply(
                lambda key: "InstrumentationKey=" + key
            ),
            ("ApplicationInsightsAgent_EXTENSION_VERSION", "~2"),
            ("WEBSITES_ENABLE_APP_SERVICE_STORAGE", "false"),
            ("DOCKER_REGISTRY_SERVER_URL", "https://index.docker.io/v1"),
            ("DOCKER_ENABLE_CI", "true"),
            ("CROP_SQL_HOST", crop_sql_host),
            ("CROP_SQL_PASS", SQL_SERVER_PASSWORD),
            ("CROP_SQL_PORT", "5432"),
            ("CROP_SQL_USER", crop_sql_user),
            ("CROP_SQL_USERNAME", SQL_SERVER_USER),
            ("CROP_SQL_DBNAME", SQL_DB_NAME),
            ("CROP_DEFAULT_USER_PASS", f"{DEFAULT_USER_PASSWORD}"),
        )
    ]
    webapp = web.WebApp(
        f"{RESOURCE_NAME_PREFIX}-webapp",
        resource_group_name=resource_group.name,
        server_farm_id=app_service_plan.id,
        site_config=web.SiteConfigArgs(
            app_settings=webapp_settings,
            always_on=True,
            linux_fx_version=f"DOCKER|{WEBAPP_DOCKER_URL}",
        ),
        https_only=True,
    )
    return webapp


def create_ingress_fa(
    resource_group, app_service_plan, sql_server, app_insights, sa_connection_string
):
    crop_sql_host = Output.format("{0}.postgres.database.azure.com", sql_server.name)
    crop_sql_user = Output.format(f"{SQL_SERVER_USER}@{0}", sql_server.name)
    ingress_fa_settings = [
        web.NameValuePairArgs(name=name, value=value)
        for name, value in (
            ("AzureWebJobsStorage", sa_connection_string),
            (
                "APPINSIGHTS_INSTRUMENTATIONKEY",
                app_insights.instrumentation_key,
            ),
            (
                "APPLICATIONINSIGHTS_CONNECTION_STRING",
                app_insights.instrumentation_key.apply(
                    lambda key: "InstrumentationKey=" + key
                ),
            ),
            ("FUNCTIONS_EXTENSION_VERSION", "~3"),
            ("WEBSITES_ENABLE_APP_SERVICE_STORAGE", "false"),
            ("DOCKER_REGISTRY_SERVER_URL", "https://index.docker.io/v1"),
            ("DOCKER_ENABLE_CI", "true"),
            ("CROP_SQL_HOST", crop_sql_host),
            ("CROP_SQL_PASS", SQL_SERVER_PASSWORD),
            ("CROP_SQL_PORT", "5432"),
            ("CROP_SQL_USER", crop_sql_user),
            ("CROP_SQL_USERNAME", SQL_SERVER_USER),
            ("CROP_SQL_DBNAME", SQL_DB_NAME),
            ("CROP_HYPER_APIKEY", HYPER_APIKEY),
            ("CROP_OPENWEATHERMAP_APIKEY", OPENWEATHERMAP_APIKEY),
            ("CROP_STARK_PASS", STARK_PASSWORD),
            ("CROP_STARK_USERNAME", STARK_USERNAME),
            ("GROWAPP_DATABASE", GROWAPP_DATABASE),
            ("GROWAPP_IP", GROWAPP_IP),
            ("GROWAPP_PASS", GROWAPP_PASSWORD),
            ("GROWAPP_SCHEMA", GROWAPP_SCHEMA),
            ("GROWAPP_USERNAME", GROWAPP_USERNAME),
        )
    ]
    ingress_app = web.WebApp(
        f"{RESOURCE_NAME_PREFIX}-ingress-fa",
        resource_group_name=resource_group.name,
        kind="functionapp",
        server_farm_id=app_service_plan.id,
        site_config=web.SiteConfigArgs(
            app_settings=ingress_fa_settings,
            linux_fx_version=f"DOCKER|{INGRESSFUNCTIONS_DOCKER_URL}",
        ),
        https_only=True,
    )
    return ingress_app


def create_fileshare(resource_group, storage_account):
    models_fa_fileshare = storage.FileShare(
        f"{RESOURCE_NAME_PREFIX}-models-share",
        account_name=storage_account.name,
        resource_group_name=resource_group.name,
        share_name=MODELS_FILESHARE_NAME,
    )
    return models_fa_fileshare


def create_share_directory(storage_account, models_fa_fileshare):
    # Note that this uses an resource type from the old pulumi_azure package, rather
    # than the new pulumi_azure_native, unlike all the other resources. The new package
    # doesn't seem to (yet?) have equivalent functionality.
    # TODO The idea is that GES would write its files in this directory. Currently
    # that's not happening though, this feature is unfinished.
    models_share_dir = azure_legacy.storage.ShareDirectory(
        f"{RESOURCE_NAME_PREFIX}-models-share-dir",
        share_name=models_fa_fileshare.name,
        storage_account_name=storage_account.name,
        name=GES_DATA_DIR,
    )
    return models_share_dir


def create_models_fa(
    resource_group,
    app_service_plan,
    sql_server,
    app_insights,
    sa_connection_string,
    storage_account,
    models_fa_fileshare,
    models_share_dir,
):
    crop_sql_host = Output.format("{0}.postgres.database.azure.com", sql_server.name)
    crop_sql_user = Output.format(f"{SQL_SERVER_USER}@{0}", sql_server.name)
    models_fa_settings = [
        web.NameValuePairArgs(name=name, value=value)
        for name, value in (
            ("AzureWebJobsStorage", sa_connection_string),
            (
                "APPINSIGHTS_INSTRUMENTATIONKEY",
                app_insights.instrumentation_key,
            ),
            (
                "APPLICATIONINSIGHTS_CONNECTION_STRING",
                app_insights.instrumentation_key.apply(
                    lambda key: "InstrumentationKey=" + key
                ),
            ),
            ("FUNCTIONS_EXTENSION_VERSION", "~3"),
            ("WEBSITES_ENABLE_APP_SERVICE_STORAGE", "false"),
            ("DOCKER_REGISTRY_SERVER_URL", "https://index.docker.io/v1"),
            ("DOCKER_ENABLE_CI", "true"),
            ("CROP_SQL_HOST", crop_sql_host),
            ("CROP_SQL_PASS", SQL_SERVER_PASSWORD),
            ("CROP_SQL_PORT", "5432"),
            ("CROP_SQL_USER", crop_sql_user),
            ("CROP_SQL_USERNAME", SQL_SERVER_USER),
            ("CROP_SQL_DBNAME", SQL_DB_NAME),
            ("CROP_DATA_DIR", f"/{GES_DATA_DIR}"),
        )
    ]
    models_app = web.WebApp(
        f"{RESOURCE_NAME_PREFIX}-models-fa",
        resource_group_name=resource_group.name,
        kind="functionapp",
        server_farm_id=app_service_plan.id,
        site_config=web.SiteConfigArgs(
            app_settings=models_fa_settings,
            linux_fx_version=f"DOCKER|{MODELFUNCTIONS_DOCKER_URL}",
            azure_storage_accounts=web.AzureStorageInfoValueArgs(
                account_name=storage_account.name,
                share_name=models_fa_fileshare.name,
                mount_path=models_share_dir.name,
                type=web.AzureStorageType.AZURE_FILES,
            ),
        ),
        https_only=True,
    )
    return models_app


def create_postgres_firewall_rules(
    resource_group, sql_server, ips_string, already_created, num_hash_chars=4
):
    """Given a list of comma separated IP addresses, create a firewall rule for the
    Postgres server to allow each one of them.

    We append a part of the IPs hash to the name, to create a unique name for the role.
    We use the hash rather than the actual IP to not reveal actual IPs in the resource
    names.
    """
    rules = []
    for ip in ips_string.split(","):
        if ip in already_created:
            # Don't try to create another rule for this same IP, if it comes up again.
            continue
        h = hashlib.sha256(bytes(ip, encoding="utf8")).hexdigest()[:num_hash_chars]
        rules.append(
            postgresql.FirewallRule(
                f"{RESOURCE_NAME_PREFIX}-fwr{h}",
                resource_group_name=resource_group.name,
                start_ip_address=ip,
                end_ip_address=ip,
                server_name=sql_server.name,
            )
        )
        already_created.append(ip)
    return rules


def main():
    resource_group = resource.ResourceGroup(f"{RESOURCE_NAME_PREFIX}-rg")
    sql_server = create_sql_server(resource_group)
    create_pg_database(resource_group, sql_server)
    app_service_plan = create_app_service_plan(resource_group)
    app_insights = create_app_insights(resource_group)
    storage_account = create_storage_account(resource_group)
    sa_connection_string = get_connection_string(
        storage_account.name, resource_group.name
    )
    webapp = create_webapp(resource_group, app_service_plan, sql_server, app_insights)
    ingress_app = create_ingress_fa(
        resource_group, app_service_plan, sql_server, app_insights, sa_connection_string
    )
    fileshare = create_fileshare(resource_group, storage_account)
    share_dir = create_share_directory(storage_account, fileshare)
    create_models_fa(
        resource_group,
        app_service_plan,
        sql_server,
        app_insights,
        sa_connection_string,
        storage_account,
        fileshare,
        share_dir,
    )

    # Create firewall rules for allowing traffic for the PostgreSQL server.
    # Using apply in this way explicitly breaks the Pulumi docs' warning that one
    # shouldn't create new resources within apply. However, this is also how some
    # officially Pulumi examples do it, and I don't there's another way. (Ideally we
    # would need a function from Option[list] to list[Option].) I think this might mean
    # that `pulumi preview` doesn't work correctly though, it might not show the
    # firewall rules.
    firewall_ips = []
    webapp.outbound_ip_addresses.apply(
        lambda x: create_postgres_firewall_rules(
            resource_group, sql_server, x, firewall_ips
        )
    )
    ingress_app.outbound_ip_addresses.apply(
        lambda x: create_postgres_firewall_rules(
            resource_group, sql_server, x, firewall_ips
        )
    )
    if POSTGRES_ALLOWED_IPS is not None:
        create_postgres_firewall_rules(
            resource_group, sql_server, POSTGRES_ALLOWED_IPS, firewall_ips
        )

    export(
        "endpoint",
        webapp.default_host_name.apply(lambda endpoint: "https://" + endpoint),
    )


if __name__ == "__main__":
    main()
