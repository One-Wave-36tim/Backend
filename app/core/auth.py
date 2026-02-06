from fastapi import Depends


def get_current_user_id() -> int:
    # TEMP: hardcode user until JWT auth is restored
    return 1


CurrentUserId = Depends(get_current_user_id)
