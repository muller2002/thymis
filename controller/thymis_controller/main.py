import asyncio
import importlib
import logging
import pathlib
import shutil
import tempfile
from contextlib import asynccontextmanager

import thymis_controller.lib  # pylint: disable=unused-import
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import engine_from_config
from thymis_controller.config import global_settings
from thymis_controller.database.base import Base
from thymis_controller.database.connection import engine
from thymis_controller.routers import api, auth, frontend

logger = logging.getLogger(__name__)

# run database migrations
alembic_config = Config(global_settings.ALEMBIC_INI_PATH)
script = ScriptDirectory.from_config(alembic_config)


def peform_db_upgrade():
    with engine.begin() as connection:
        alembic_config.attributes["connection"] = connection
        logger.info("Performing database upgrade")
        command.upgrade(alembic_config, "head")
        logger.info("Database upgrade complete")


def check_and_move_old_repo():
    assert (
        global_settings.REPO_PATH != "/var/lib/thymis"
    ), "REPO_PATH should not be /var/lib/thymis"
    # check if old repo path exists
    old_path = pathlib.Path("/var/lib/thymis")
    old_git_path = old_path / ".git"
    if old_git_path.exists():
        logger.warning(
            f"Old git repository found at {old_git_path}, moving to {global_settings.REPO_PATH}"
        )
        # move the /var/lib/thymis directory to temp
        with tempfile.TemporaryDirectory() as tempdir:
            tempdir_path = pathlib.Path(tempdir)
            # copy /var/lib/thymis to temp
            shutil.copytree(old_path, tempdir_path / "thymis")
            # remove all files in /var/lib/thymis without removing the directory
            for file in old_path.iterdir():
                if file.is_dir():
                    shutil.rmtree(file)
                else:
                    file.unlink()
            # move the old directory to the new one
            shutil.move(tempdir_path / "thymis", global_settings.REPO_PATH)
            # remove the temp directory
            shutil.rmtree(tempdir_path)
        logger.info(f"Moved old git repository to {global_settings.REPO_PATH}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up...")
    check_and_move_old_repo()
    peform_db_upgrade()
    logger.info("starting frontend")
    await frontend.frontend.run()
    logger.info("frontend started")
    asyncio.get_event_loop().create_task(frontend.frontend.raise_if_terminated())
    logger.info("frontend raise_if_terminated task created")
    logger.info("Starting controller at \033[1m%s\033[0m", global_settings.BASE_URL)
    yield
    logger.info("stopping frontend")
    await frontend.frontend.stop()
    logger.info("frontend stopped")


description = """
API to control Nix operating system 🎛️
"""

app = FastAPI(
    title="Thymis Controller API",
    description=description,
    summary="Controller backend for gathering and changing information of a device",
    version="0.1.0",
    contact={
        "name": "Thymis",
        "url": "https://thymis.io",
        "email": "software@thymis.io",
    },
    license_info={
        "name": "AGPLv3",
        "url": "https://www.gnu.org/licenses/agpl-3.0.en.html",
    },
    servers=[
        {
            "url": global_settings.BASE_URL,
            "description": "Thymis Controller",
        },
    ],
    lifespan=lifespan,
)

origins = [
    # TODO remove development origins
    "http://localhost",
    "http://localhost:5173",
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    # allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth")
app.include_router(api.router, prefix="/api")
app.include_router(frontend.router)


if importlib.util.find_spec("thymis_enterprise"):
    import thymis_enterprise  # pylint: disable=import-error # type: ignore

    thymis_enterprise.thymis_enterprise_hello_world()
