import datetime
from fastapi import Depends, HTTPException, status
from fastapi.param_functions import Form
from fastapi.security import OAuth2PasswordBearer, SecurityScopes

from jose import jwt
from typing import Optional


APP_NAME = 'myapp'

# in a productive app, DO NOT leave this in your code
# ACTION ITEM: replace this with a proper secret you come up with
# this secret is used to sign the access tokens, allowing jose to verify that they have not been tampered with
TOKEN_SECRET = 'YOUR TOKEN SECRET HERE'

# ACTION ITEM: replace these scopes with your own scopes. If you don't need any, leave the dict empty
SCOPES = {
    'some.scope': 'Can access endpoint1',
    'other.scope': 'Can access endpoint2',
    'third.scope': 'Can access both endpoint1 and endpoint2'
}

# used to en-/decode the JWT tokens. Only modify if you know what you're doing
ALGORITHM = 'HS256'


# define the oauth scheme
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes=SCOPES,
)


class OAuth2Form:
    """container class to capture the form inputs from the login page
    """

    def __init__(
        self,
        username: str = Form(),
        password: str = Form(),
        scope: list[str] = Form(default=[])
    ):
        self.username = username
        self.password = password
        self.scopes = scope


def create_access_token(data: dict, expiry_seconds: Optional[int] = 60 * 60 * 24 * 7  # one week, in seconds
                        ) -> str:
    """create an access token from a given dict of data
    Parameters
    ----------
        data: dictionary
            the data to include in the token
        expiry_seconds: timedelta or None
            how long the token should be valid for. Defaults to one week

    Returns
    -------
        string
            the JWT-encoded access token
    """

    to_encode = data.copy()

    # add expiry date
    expiry_date = datetime.datetime.utcnow() + datetime.timedelta(seconds=expiry_seconds)
    to_encode.update({'expires_at': expiry_date.timestamp()})

    # encode and return
    encoded_jwt = jwt.encode(to_encode, TOKEN_SECRET, algorithm=ALGORITHM)
    return encoded_jwt


def validate_token(token: dict) -> bool:
    """ensure the token is valid (i.e. issued by us and not expired)
    """

    return token.get('issuer') == APP_NAME and token.get('expires_at', 0) > datetime.datetime.utcnow().timestamp()


async def ensure_permissions(security_scopes: SecurityScopes, token: str = Depends(oauth2_scheme)):
    """ensure the provided token has enough permissions to access the requested resource
    """

    decoded_token = jwt.decode(token, TOKEN_SECRET, algorithms=[ALGORITHM])

    # check if the token is valid
    if not validate_token(decoded_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Could not validate credentials'
        )

    # check if the provided token has any of the necessary scopes
    if not has_any_scope(security_scopes.scopes, decoded_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Insufficient permissions'
        )


def has_any_scope(scopes: list[str], token_data: dict) -> bool:
    """check if a token has any of the required scopes.
    Similarly, you can build `has_all_scopes` or arbitrary other checks to extend or replace this check
    """

    if not scopes:  # no scopes required, always go through
        return True
    return any(scope in scopes for scope in token_data.get('scopes', '').split())


def validate_login(username: str, password: str) -> bool:
    """validate username/password against the credentials you have stored
    IMPORTANT NOTE: never, ever store credentials in plain text, always use some form of encryption
    one way of doing that is `passlib`'s CryptContext

    Parameters
    ----------
        username: string
        password: string

    Returns
    -------
        bool
            whether or not the user login was successfully validated
    """

    # ACTION ITEM: replace this with proper logic to validate the provided credentials
    return True
