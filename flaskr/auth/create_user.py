from email_validator import validate_email, EmailNotValidError
from werkzeug.security import generate_password_hash
from password_strength import PasswordPolicy

from flaskr.auth.auth_database.repository import Repository
from flaskr.auth.auth_database.factory import Factory
from flaskr.framework.model.request.response import Response


def check_password(password) -> []:
    policy = PasswordPolicy.from_names(
        length=8,  # min length: 8
        uppercase=1,  # need min. 2 uppercase letters
        numbers=1,  # need min. 2 digits
        nonletters=2,  # need min. 2 non-letter characters (digits, specials, anything)
    )
    results = policy.password(password)
    return round(results.strength(), 2)


def check_entries(email: str, username: str, password: str) -> Response:
    # validate email
    try:
        valid = validate_email(email)
        email = valid.email
    except EmailNotValidError as e:
        return Response(False, str(e))

    # validate password
    password_strength = check_password(password)
    if password_strength < .2:
        return Response(False, "Please make your password more complex. Strength of password: %s" % password_strength)

    # validate registration changes are allowed
    user_repository = Repository()
    user = user_repository.get_by_email(email)
    if user is None:
        return Response(False, "Account changes are not permitted for this email. "
                               "Please contact the admin if this is in error.")

    # validate username is not already in use
    username_results = user_repository.filter_by_username(username)
    for item in username_results:
        if item['email'] != email:
            return Response(False, 'Username is already taken.')

    return Response(True, '')


def create_user(email: str,
                username: str,
                password: str,
                permission: int,
                organization: str,
                token) -> Response:
    user_repository = Repository()
    user_factory = Factory()

    if user_repository.get_by_username(username) is not None:
        return Response(False, 'Username is already taken.')
    if user_repository.get_by_email(email) is not None:
        return Response(False, 'Email is already registered.')

    data = {'email': email,
            'username': username,
            'password': generate_password_hash(password),
            'permission': permission,
            'organization': organization,
            'token': token}

    data = user_factory.create(data)
    user_repository.save(data)
    return Response(True, '')
