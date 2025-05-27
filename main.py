from mp2 import Mp2Client, tokenize_command
from validators import *

AUTHENTICATED_ADMIN = None
ANON_USER = "GUEST"
ANON_USER_ID = None
POSTGRESQL_CONFIG_FILE_NAME = "database.cfg"

def print_success_msg(message):
    print(message)


def print_error_msg(message):
    print("ERROR: %s" % message)


def print_admin_info(admin):
    global ANON_USER

    if admin:
        print(admin, end=" > ")
    else:
        print(ANON_USER, end=" > ")


def main():
    global AUTHENTICATED_ADMIN, POSTGRESQL_CONFIG_FILE_NAME, ANON_USER_ID

    client = Mp2Client(config_filename=POSTGRESQL_CONFIG_FILE_NAME)
    ANON_USER_ID = client.user.user_id
    client.help()

    while True:
        # print customer information if signed in
        print_admin_info(admin=AUTHENTICATED_ADMIN)

        # get new command from user
        cmd_text = input()
        cmd_tokens = tokenize_command(cmd_text)
        cmd = cmd_tokens[0] if len(cmd_tokens) > 0 else ""

        if cmd == "help":
            client.help()

        elif cmd == "sign_up":
            # validate command
            validation_result, validation_message = sign_up_validator(AUTHENTICATED_ADMIN, cmd_tokens)

            if validation_result:
                client.connect()
                _, arg_seller_id, arg_password, arg_plan_id = cmd_tokens

                # sign up
                exec_success, exec_message = client.sign_up(admin_id=arg_seller_id, password=arg_password, level_id=arg_plan_id)

                client.disconnect()

                # print message
                if exec_success:
                    print_success_msg(exec_message)
                else:
                    print_error_msg(exec_message)

            else:
                print_error_msg(validation_message)

        elif cmd == "sign_in":
            # validate command
            validation_result, validation_message = sign_in_validator(AUTHENTICATED_ADMIN, cmd_tokens)

            if validation_result:
                _, arg_seller_id, arg_password = cmd_tokens

                client.connect()
                seller, exec_message = client.sign_in(admin_id=arg_seller_id, password=arg_password)

                if seller:
                    ANON_USER_ID = None
                    AUTHENTICATED_ADMIN = seller
                    print_success_msg(exec_message)
                else:
                    print_error_msg(exec_message)

            else:
                print_error_msg(validation_message)

        elif cmd == "sign_out":
            # validate command
            validation_result, validation_message = basic_validator(AUTHENTICATED_ADMIN, cmd_tokens)
            client.connect()
            if validation_result:
                exec_success, exec_message = client.sign_out(admin=AUTHENTICATED_ADMIN)

                if exec_success:
                    ANON_USER_ID = client.user.user_id
                    AUTHENTICATED_ADMIN = None
                    print_success_msg(exec_message)

                else:
                    print_error_msg(exec_message)

            else:
                print_error_msg(validation_message)
            client.disconnect()

        elif cmd == "quit":
            client.connect()
            # validate command
            validation_result, validation_message = quit_validator(cmd_tokens)

            if validation_result:

                exec_success, exec_message = client.quit(admin=AUTHENTICATED_ADMIN)

                if exec_success:
                    client.disconnect()
                    break
                else:
                    print_error_msg(exec_message)

            else:
                print_error_msg(validation_message)
            client.disconnect()
        
        elif cmd == "show_levels":
            # validate command
            client.connect()
            exec_success, exec_message = client.show_levels()
            client.disconnect()
            if exec_success:
                print_success_msg(exec_message)
            else:
                print_error_msg(exec_message)
        
        elif cmd == "show_my_level":
            # validate command
            client.connect()
            exec_success, exec_message = client.show_my_level(admin=AUTHENTICATED_ADMIN)
            client.disconnect()
            if exec_success:
                print_success_msg(exec_message)
            else:
                print_error_msg(exec_message)

        elif cmd == "change_level":
            # validate command
            client.connect()
            validation_result, validation_message = change_level_validator(cmd_tokens)

            if validation_result:
                _, arg_plan_id = cmd_tokens

                seller, exec_message = client.change_level(admin=AUTHENTICATED_ADMIN, new_level_id=arg_plan_id)

                if seller:
                    AUTHENTICATED_ADMIN = seller
                    print_success_msg(exec_message)

                else:
                    print_error_msg(exec_message)

            else:
                print_error_msg(validation_message)
            client.disconnect()
        elif cmd == "get_statistics":
            # validate command
            client.connect()
            validation_result, validation_message = get_statistics_validator(cmd_tokens)

            if validation_result:
                if len(cmd_tokens) == 3:
                    _, name, arg_country_name = cmd_tokens
                elif len(cmd_tokens) == 2:
                    _, name = cmd_tokens
                    arg_country_name = None

                exec_success, exec_message = client.get_statistics(name=name, country_name=arg_country_name)

                if exec_success:
                    print_success_msg(exec_message)
                else:
                    print_error_msg(exec_message)

            else:
                print_error_msg(validation_message)
            client.disconnect()
        
        elif cmd == "update_religion":
            # validate command
            client.connect()
            validation_result, validation_message = update_religion_validator(cmd_tokens)

            if validation_result:
                _, country_name, religion_name1, religion_name2, percentage = cmd_tokens

                exec_success, exec_message = client.update_religion(
                    admin=AUTHENTICATED_ADMIN,
                    country_name=country_name,
                    religion_name1=religion_name1,
                    religion_name2=religion_name2,
                    percentage=percentage
                )

                if exec_success:
                    print_success_msg(exec_message)
                else:
                    print_error_msg(exec_message)

            else:
                print_error_msg(validation_message)
            client.disconnect()
        elif cmd == "transfer_city":
            # validate command
            client.connect()
            validation_result, validation_message = transfer_city_validator(cmd_tokens)

            if validation_result:
                _, city_name, current_country, new_country = cmd_tokens

                exec_success, exec_message = client.transfer_city(
                    admin=AUTHENTICATED_ADMIN,
                    city_name=city_name,
                    current_country=current_country,
                    new_country=new_country
                )

                if exec_success:
                    print_success_msg(exec_message)
                else:
                    print_error_msg(exec_message)

            else:
                print_error_msg(validation_message)
            client.disconnect()
        
        elif cmd == "adjust_population":
            # validate command
            client.connect()
            validation_result, validation_message = adjust_population_validator(cmd_tokens)

            if validation_result:
                if len(cmd_tokens) == 4:
                    _, name, country_name, new_population = cmd_tokens
                elif len(cmd_tokens) == 3:
                    _, name, new_population = cmd_tokens
                    country_name = None

                exec_success, exec_message = client.adjust_population(
                    admin=AUTHENTICATED_ADMIN,
                    name=name,
                    country_name=country_name,
                    new_population=new_population
                )

                if exec_success:
                    print_success_msg(exec_message)
                else:
                    print_error_msg(exec_message)

            else:
                print_error_msg(validation_message)
            client.disconnect()

        elif cmd == "":
            pass

        else:
            print_error_msg(messages.CMD_UNDEFINED)


if __name__ == '__main__':
    main()
