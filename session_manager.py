import requests

_session = None


def create_session():
    global _session
    if _session:
        _session.close()
    _session = requests.Session()


def close_session():
    global _session
    if _session:
        _session.close()
        _session = None


def get_session():
    return _session


def test_connection(base_url, endpoint="/api/tags", timeout=6):
    session = get_session()
    if session is None:
        return False, "No active session"

    url = f"{base_url.rstrip('/')}{endpoint}"

    try:
        response = session.get(url, timeout=timeout)
        response.raise_for_status()
        return True, "Connection established"

    except requests.exceptions.ConnectTimeout:
        return False, "Connection timed out"

    except requests.exceptions.ConnectionError:
        return False, "Could not connect to API"

    except requests.exceptions.HTTPError as e:
        return False, f"HTTP error: {e.response.status_code}"

    except Exception as e:
        return False, str(e)


def create_and_test(base_url, endpoint="/api/tags"):
    create_session()
    ok, msg = test_connection(base_url, endpoint)

    if not ok:
        close_session()

    return ok, msg


def has_session():
    return _session is not None
