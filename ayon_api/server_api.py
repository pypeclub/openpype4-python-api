import os
import socket

from .constants import (
    SERVER_URL_ENV_KEY,
    SERVER_TOKEN_ENV_KEY,
)
from .server import ServerAPI
from .exceptions import FailedServiceInit


class GlobalServerAPI(ServerAPI):
    """Extended server api which also handles storing tokens and url.

    Created object expect to have set environment variables
    'AYON_SERVER_URL'. Also is expecting filled 'AYON_TOKEN'
    but that can be filled afterwards with calling 'login' method.
    """

    def __init__(self):
        url = self.get_url()
        token = self.get_token()

        super(GlobalServerAPI, self).__init__(url, token)

        self.validate_server_availability()
        self.create_session()

    def login(self, username, password):
        """Login to the server or change user.

        If user is the same as current user and token is available the
        login is skipped.
        """

        previous_token = self._access_token
        super(GlobalServerAPI, self).login(username, password)
        if self.has_valid_token and previous_token != self._access_token:
            os.environ[SERVER_TOKEN_ENV_KEY] = self._access_token

    @staticmethod
    def get_url():
        return os.environ.get(SERVER_URL_ENV_KEY)

    @staticmethod
    def get_token():
        return os.environ.get(SERVER_TOKEN_ENV_KEY)

    @staticmethod
    def set_environments(url, token):
        """Change url and token environemnts in currently running process.

        Args:
            url (str): New server url.
            token (str): User's token.
        """

        os.environ[SERVER_URL_ENV_KEY] = url or ""
        os.environ[SERVER_TOKEN_ENV_KEY] = token or ""


class GlobalContext:
    """Singleton connection holder.

    Goal is to avoid create connection on import which can be dangerous in
    some cases.
    """

    _connection = None

    @classmethod
    def is_connection_created(cls):
        return cls._connection is not None

    @classmethod
    def change_token(cls, url, token):
        GlobalServerAPI.set_environments(url, token)
        if cls._connection is None:
            return

        if cls._connection.get_base_url() == url:
            cls._connection.set_token(token)
        else:
            cls.close_connection()

    @classmethod
    def close_connection(cls):
        if cls._connection is not None:
            cls._connection.close_session()
        cls._connection = None

    @classmethod
    def get_server_api_connection(cls):
        if cls._connection is None:
            cls._connection = GlobalServerAPI()
        return cls._connection


class ServiceContext:
    """Helper for services running under server.

    When service is running from server the process receives information about
    connection from environment variables. This class helps to initialize the
    values without knowing environment variables (that may change over time).

    All what must be done is to call 'init_service' function/method. The
    arguments are for cases when the service is running in specific environment
    and their values are e.g. loaded from private file or for testing purposes.
    """

    token = None
    server_url = None
    addon_name = None
    addon_version = None
    service_name = None

    @staticmethod
    def get_value_from_envs(env_keys, value=None):
        if value:
            return value

        for env_key in env_keys:
            value = os.environ.get(env_key)
            if value:
                break
        return value

    @classmethod
    def init_service(
        cls,
        token=None,
        server_url=None,
        addon_name=None,
        addon_version=None,
        service_name=None,
        connect=True
    ):
        token = cls.get_value_from_envs(
            ("AY_API_KEY", "AYON_TOKEN"),
            token
        )
        server_url = cls.get_value_from_envs(
            ("AY_SERVER_URL", "AYON_SERVER_URL"),
            server_url
        )
        if not server_url:
            raise FailedServiceInit("URL to server is not set")

        if not token:
            raise FailedServiceInit(
                "Token to server {} is not set".format(server_url)
            )

        addon_name = cls.get_value_from_envs(
            ("AY_ADDON_NAME", "AYON_ADDON_NAME"),
            addon_name
        )
        addon_version = cls.get_value_from_envs(
            ("AY_ADDON_VERSION", "AYON_ADDON_VERSION"),
            addon_version
        )
        service_name = cls.get_value_from_envs(
            ("AY_SERVICE_NAME", "AYON_SERVICE_NAME"),
            service_name
        )

        cls.token = token
        cls.server_url = server_url
        cls.addon_name = addon_name
        cls.addon_version = addon_version
        cls.service_name = service_name or socket.gethostname()

        # Make sure required environments for GlobalServerAPI are set
        GlobalServerAPI.set_environments(cls.server_url, cls.token)

        if connect:
            print("Connecting to server \"{}\"".format(server_url))
            con = GlobalContext.get_server_api_connection()
            user = con.get_user()
            print("Logged in as user \"{}\"".format(user["name"]))


def init_service(*args, **kwargs):
    ServiceContext.init_service(*args, **kwargs)


def is_connection_created():
    """Is global connection created.

    Returns:
        bool: True if connection was connected.
    """

    return GlobalContext.is_connection_created()


def close_connection():
    """Close global connection if is connected."""

    GlobalContext.close_connection()


def change_token(url, token):
    """Change connection token for url.

    This function can be also used to change url.

    Args:
        url (str): Server url.
        token (str): API key token.
    """

    GlobalContext.change_token(url, token)


def set_environments(url, token):
    """Set global environments for global connection.

    Args:
        url (Union[str, None]): Url to server or None to unset environments.
        token (Union[str, None]): API key token to be used for connection.
    """

    GlobalServerAPI.set_environments(url, token)


def get_server_api_connection():
    """Access to global scope object of GlobalServerAPI.

    This access expect to have set environment variables 'AYON_SERVER_URL'
    and 'AYON_TOKEN'.

    Returns:
        GlobalServerAPI: Object of connection to server.
    """

    return GlobalContext.get_server_api_connection()


def get_base_url():
    con = get_server_api_connection()
    return con.get_base_url()


def get_rest_url():
    con = get_server_api_connection()
    return con.get_rest_url()


def raw_get(*args, **kwargs):
    con = get_server_api_connection()
    return con.raw_get(*args, **kwargs)


def raw_post(*args, **kwargs):
    con = get_server_api_connection()
    return con.raw_post(*args, **kwargs)


def raw_put(*args, **kwargs):
    con = get_server_api_connection()
    return con.raw_put(*args, **kwargs)


def raw_patch(*args, **kwargs):
    con = get_server_api_connection()
    return con.raw_patch(*args, **kwargs)


def raw_delete(*args, **kwargs):
    con = get_server_api_connection()
    return con.raw_delete(*args, **kwargs)


def get(*args, **kwargs):
    con = get_server_api_connection()
    return con.get(*args, **kwargs)


def post(*args, **kwargs):
    con = get_server_api_connection()
    return con.post(*args, **kwargs)


def put(*args, **kwargs):
    con = get_server_api_connection()
    return con.put(*args, **kwargs)


def patch(*args, **kwargs):
    con = get_server_api_connection()
    return con.patch(*args, **kwargs)


def delete(*args, **kwargs):
    con = get_server_api_connection()
    return con.delete(*args, **kwargs)


def get_event(*args, **kwargs):
    con = get_server_api_connection()
    return con.get_event(*args, **kwargs)


def get_events(*args, **kwargs):
    con = get_server_api_connection()
    return con.get_events(*args, **kwargs)


def dispatch_event(*args, **kwargs):
    con = get_server_api_connection()
    return con.dispatch_event(*args, **kwargs)


def update_event(*args, **kwargs):
    con = get_server_api_connection()
    return con.update_event(*args, **kwargs)


def enroll_event_job(*args, **kwargs):
    con = get_server_api_connection()
    return con.enroll_event_job(*args, **kwargs)


def download_file(*args, **kwargs):
    con = get_server_api_connection()
    return con.download_file(*args, **kwargs)


def upload_file(*args, **kwargs):
    con = get_server_api_connection()
    return con.upload_file(*args, **kwargs)


def query_graphql(*args, **kwargs):
    con = get_server_api_connection()
    return con.query_graphql(*args, **kwargs)


def get_users(*args, **kwargs):
    con = get_server_api_connection()
    return con.get_users(*args, **kwargs)


def get_user(*args, **kwargs):
    con = get_server_api_connection()
    return con.get_user(*args, **kwargs)


def get_attributes_for_type(*args, **kwargs):
    con = get_server_api_connection()
    return con.get_attributes_for_type(*args, **kwargs)


def get_addons_info(*args, **kwargs):
    con = get_server_api_connection()
    return con.get_addons_info(*args, **kwargs)


def download_addon_private_file(*args, **kwargs):
    con = get_server_api_connection()
    return con.download_addon_private_file(*args, **kwargs)


def get_dependencies_info(*args, **kwargs):
    con = get_server_api_connection()
    return con.get_dependencies_info(*args, **kwargs)


def update_dependency_info(*args, **kwargs):
    con = get_server_api_connection()
    return con.update_dependency_info(*args, **kwargs)


def download_dependency_package(*args, **kwargs):
    con = get_server_api_connection()
    return con.download_dependency_package(*args, **kwargs)


def upload_dependency_package(*args, **kwargs):
    con = get_server_api_connection()
    return con.upload_dependency_package(*args, **kwargs)


def delete_dependency_package(*args, **kwargs):
    con = get_server_api_connection()
    return con.delete_dependency_package(*args, **kwargs)


def get_project_anatomy_presets(*args, **kwargs):
    con = get_server_api_connection()
    return con.get_project_anatomy_presets(*args, **kwargs)


def get_project_anatomy_preset(*args, **kwargs):
    con = get_server_api_connection()
    return con.get_project_anatomy_preset(*args, **kwargs)


def get_full_production_settings(*args, **kwargs):
    con = get_server_api_connection()
    return con.get_full_production_settings(*args, **kwargs)


def get_production_settings(*args, **kwargs):
    con = get_server_api_connection()
    return con.get_production_settings(*args, **kwargs)


def get_full_project_settings(*args, **kwargs):
    con = get_server_api_connection()
    return con.get_full_project_settings(*args, **kwargs)


def get_project_settings(*args, **kwargs):
    con = get_server_api_connection()
    return con.get_project_settings(*args, **kwargs)


def get_addon_settings(*args, **kwargs):
    con = get_server_api_connection()
    return con.get_addon_settings(*args, **kwargs)


def get_project(*args, **kwargs):
    con = get_server_api_connection()
    return con.get_project(*args, **kwargs)


def get_projects(*args, **kwargs):
    con = get_server_api_connection()
    return con.get_projects(*args, **kwargs)


def get_folders(*args, **kwargs):
    con = get_server_api_connection()
    return con.get_folders(*args, **kwargs)


def get_tasks(*args, **kwargs):
    con = get_server_api_connection()
    return con.get_tasks(*args, **kwargs)


def get_folder_by_id(*args, **kwargs):
    con = get_server_api_connection()
    return con.get_folder_by_id(*args, **kwargs)


def get_folder_by_path(*args, **kwargs):
    con = get_server_api_connection()
    return con.get_folder_by_path(*args, **kwargs)


def get_folder_by_name(*args, **kwargs):
    con = get_server_api_connection()
    return con.get_folder_by_name(*args, **kwargs)


def get_folder_ids_with_subsets(*args, **kwargs):
    con = get_server_api_connection()
    return con.get_folder_ids_with_subsets(*args, **kwargs)


def get_subsets(*args, **kwargs):
    con = get_server_api_connection()
    return con.get_subsets(*args, **kwargs)


def get_subset_by_id(*args, **kwargs):
    con = get_server_api_connection()
    return con.get_subset_by_id(*args, **kwargs)


def get_subset_by_name(*args, **kwargs):
    con = get_server_api_connection()
    return con.get_subset_by_name(*args, **kwargs)


def get_subset_families(*args, **kwargs):
    con = get_server_api_connection()
    return con.get_subset_families(*args, **kwargs)


def get_versions(*args, **kwargs):
    con = get_server_api_connection()
    return con.get_versions(*args, **kwargs)


def get_version_by_id(*args, **kwargs):
    con = get_server_api_connection()
    return con.get_version_by_id(*args, **kwargs)


def get_version_by_name(*args, **kwargs):
    con = get_server_api_connection()
    return con.get_version_by_name(*args, **kwargs)


def get_hero_version_by_id(*args, **kwargs):
    con = get_server_api_connection()
    return con.get_hero_version_by_id(*args, **kwargs)


def get_hero_version_by_subset_id(*args, **kwargs):
    con = get_server_api_connection()
    return con.get_hero_version_by_subset_id(*args, **kwargs)


def get_hero_versions(*args, **kwargs):
    con = get_server_api_connection()
    return con.get_hero_versions(*args, **kwargs)


def get_last_versions(*args, **kwargs):
    con = get_server_api_connection()
    return con.get_last_versions(*args, **kwargs)


def get_last_version_by_subset_id(*args, **kwargs):
    con = get_server_api_connection()
    return con.get_last_version_by_subset_id(*args, **kwargs)


def get_last_version_by_subset_name(*args, **kwargs):
    con = get_server_api_connection()
    return con.get_last_version_by_subset_name(*args, **kwargs)


def version_is_latest(*args, **kwargs):
    con = get_server_api_connection()
    return con.version_is_latest(*args, **kwargs)


def get_representations(*args, **kwargs):
    con = get_server_api_connection()
    return con.get_representations(*args, **kwargs)


def get_representation_by_id(*args, **kwargs):
    con = get_server_api_connection()
    return con.get_representation_by_id(*args, **kwargs)


def get_representation_by_name(*args, **kwargs):
    con = get_server_api_connection()
    return con.get_representation_by_name(*args, **kwargs)


def get_representation_parents(*args, **kwargs):
    con = get_server_api_connection()
    return con.get_representation_parents(*args, **kwargs)


def get_representations_parents(*args, **kwargs):
    con = get_server_api_connection()
    return con.get_representations_parents(*args, **kwargs)


def create_project(
    project_name,
    project_code,
    library_project=False,
    preset_name=None
):
    con = get_server_api_connection()
    return con.create_project(
        project_name,
        project_code,
        library_project,
        preset_name
    )


def delete_project(project_name):
    con = get_server_api_connection()
    return con.delete_project(project_name)


def create_thumbnail(project_name, src_filepath):
    con = get_server_api_connection()
    return con.create_thumbnail(project_name, src_filepath)


def get_thumbnail(project_name, entity_type, entity_id, thumbnail_id=None):
    con = get_server_api_connection()
    con.get_thumbnail(project_name, entity_type, entity_id, thumbnail_id)


def get_folder_thumbnail(project_name, folder_id, thumbnail_id=None):
    con = get_server_api_connection()
    return con.get_folder_thumbnail(project_name, folder_id, thumbnail_id)


def get_version_thumbnail(project_name, version_id, thumbnail_id=None):
    con = get_server_api_connection()
    return con.get_version_thumbnail(project_name, version_id, thumbnail_id)


def get_workfile_thumbnail(project_name, workfile_id, thumbnail_id=None):
    con = get_server_api_connection()
    return con.get_workfile_thumbnail(project_name, workfile_id, thumbnail_id)


def create_thumbnail(project_name, src_filepath):
    con = get_server_api_connection()
    return con.create_thumbnail(project_name, src_filepath)


def get_default_fields_for_type(entity_type):
    con = get_server_api_connection()
    return con.get_default_fields_for_type(entity_type)
