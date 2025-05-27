import messages


def sign_up_validator(auth_admin, cmd_tokens):
    expected_args_count = 3

    if len(cmd_tokens) != expected_args_count + 1:
        return False, messages.CMD_NOT_ENOUGH_ARGS % expected_args_count

    if auth_admin:
        return False, messages.USER_ALREADY_SIGNED_IN

    return True, None


def sign_in_validator(auth_admin, cmd_tokens):
    expected_args_count = 2

    if len(cmd_tokens) != expected_args_count + 1:
        return False, messages.CMD_NOT_ENOUGH_ARGS % expected_args_count

    if auth_admin:
        if auth_admin.admin_id == cmd_tokens[1]:
            return None, messages.USER_ALREADY_SIGNED_IN
        else:
            return None, messages.USER_OTHER_SIGNED_IN
    
    return True, None


"""
    This validator is basic validator that returns (True, None) 
    when a seller is authenticated and the number of command tokens is 1.
    Returns (False, <message>) otherwise.
"""


def basic_validator(auth_admins, cmd_tokens):
    if auth_admins:
        return True, None
    elif not auth_admins and len(cmd_tokens) == 1:
        return False, messages.USER_NOT_AUTHORIZED
    else:
        return False, messages.CMD_INVALID_ARGS


def quit_validator(cmd_tokens):
    if len(cmd_tokens) == 1:
        return True, None
    else:
        return False, messages.CMD_INVALID_ARGS

# def change_level_validator(auth_admin, cmd_tokens):
def change_level_validator(cmd_tokens):
    expected_args_count = 1

    # if not auth_admin:
    #     return False, messages.USER_NOT_AUTHORIZED
    if len(cmd_tokens) != expected_args_count + 1:
        return False, messages.CMD_NOT_ENOUGH_ARGS % expected_args_count

    return True, None

def get_statistics_validator(cmd_tokens):
    expected_args_count = {1 + 1, 2 + 1}

    if len(cmd_tokens) not in expected_args_count:
        return False, messages.CMD_NOT_ENOUGH_ARGS % 2

    return True, None

def update_religion_validator(cmd_tokens):
    expected_args_count = 4

    if len(cmd_tokens) != expected_args_count + 1:
        return False, messages.CMD_NOT_ENOUGH_ARGS % expected_args_count
    
    return True, None

def transfer_city_validator(cmd_tokens):
    expected_args_count = 3

    if len(cmd_tokens) != expected_args_count + 1:
        return False, messages.CMD_NOT_ENOUGH_ARGS % expected_args_count
    
    return True, None

def adjust_population_validator(cmd_tokens):
    expected_args_count = {2 + 1, 3 + 1}

    if len(cmd_tokens) not in expected_args_count:
        return False, messages.CMD_NOT_ENOUGH_ARGS % 3
    
    return True, None









