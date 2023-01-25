from bcrypt import gensalt, hashpw
import pytest

from .conftest import check_for_docker
from core.db import session_close
from core.structure import UserClass
from core import utils

DOCKER_RUNNING = check_for_docker()


def _get_password_hash(username, email):
    """Return the password hash for the given user, or None if the user doesn't exist."""
    query = UserClass.query.filter_by(username=username, email=email)
    if query.count() > 0:
        return query.first().password
    else:
        return None


def _user_exists(username, email):
    """Return a bool for whether the given user credentials exist in the database."""
    return _get_password_hash(username, email) is not None


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_user_create_modify_delete(app):
    """Test creating a user, changing their password, and deleting them."""
    username = "vebaonstotunawoutnvscvinkowuyfsyaeovuakvsrka"
    email = "tanosrvoasntekvfwluthva`onqtoywucuyauonvozkssenatenoa"
    password1 = "tnoasriecvnulw`thfoyauncu ncxiekstovnauonfwocua"
    password2 = "v akvfztazrfitlula`tuqlfnpav`foluhkmionulh"

    with app.app_context():
        assert not _user_exists(username, email)
        utils.create_user(username, email, password1)
        assert _user_exists(username, email)

        old_hash = (
            UserClass.query.filter_by(username=username, email=email).first().password
        )
        utils.change_user_password(username, email, password2)
        assert _user_exists(username, email)
        new_hash = (
            UserClass.query.filter_by(username=username, email=email).first().password
        )
        assert old_hash != new_hash

        utils.delete_user(username, email)
        assert not _user_exists(username, email)
