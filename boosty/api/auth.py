import asyncio
from time import time
from aiohttp import ClientSession

from boosty.utils.json import dict_to_file, file_to_dict
from boosty.utils.logging import logger


class Auth:
    access_token, refresh_token, expires_at, device_id, headers = None, None, None, None, None
    DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
    """https://techblog.willshouse.com/2012/01/03/most-common-user-agents/"""

    def __init__(
            self,
            auth_file: str = "auth.json",
            user_agent: str = None,
    ):
        self.auth_file = auth_file
        self.user_agent = user_agent or self.DEFAULT_USER_AGENT
        self.load_auth_data()

    def load_auth_data(self):
        try:
            auth_dict = file_to_dict(self.auth_file)
        except FileNotFoundError:
            logger.info(f"No auth file ({self.auth_file}) was found, using blank values (anonymous access mode)")
            auth_dict = {}
        self.access_token = auth_dict.get("access_token")
        self.refresh_token = auth_dict.get("refresh_token")
        self.expires_at = auth_dict.get("expires_at")
        self.device_id = auth_dict.get("device_id")
        self.headers = {"User-Agent": self.user_agent}
        if self.access_token:
            self.headers |= {"Authorization": f"Bearer {self.access_token}"}

    def save_auth_data(self):
        auth_data = {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.expires_at,
            "device_id": self.device_id,
        }
        dict_to_file(auth_data, self.auth_file)

    def save_auth_data_dotenv(self, dotenv_file=None):
        import dotenv

        if not dotenv_file:
            dotenv_file = dotenv.find_dotenv()

        print(f".env file found: {dotenv_file}")
        dotenv.load_dotenv(dotenv_file)
        dotenv.set_key(dotenv_file, "ACCESS_TOKEN", self.access_token, "auto")
        dotenv.set_key(dotenv_file, "REFRESH_TOKEN", self.refresh_token, "auto")

    def get_auth_data(self):
        return self.access_token, self.refresh_token, self.expires_at

    async def refresh_auth_data(self, session: ClientSession):
        self.load_auth_data()

        response = await session.post(
            "/oauth/token/",
            data={
                "device_id": self.device_id,
                "device_os": "web",
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
            },
            headers=self.headers)

        response_data = await response.json()
        self.refresh_token = response_data["refresh_token"]
        self.access_token = response_data["access_token"]
        self.expires_at = int(time()) + response_data["expires_in"]

        self.save_auth_data()


async def main():
    async with ClientSession() as session:
        auth = Auth()
        await auth.refresh_auth_data(session)
        access_token, refresh_token, expires = auth.get_auth_data()
    print(f"{access_token , refresh_token , expires = }")


if __name__ == "__main__":
    asyncio.run(main())
