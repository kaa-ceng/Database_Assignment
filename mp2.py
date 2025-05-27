import psycopg2
import uuid
from datetime import datetime

from config import read_config
from messages import *
from admin import Administrator, User

"""
    Splits given command string by spaces and trims each token.
    Returns token list. also handles quoted strings.
"""
def tokenize_command(command):
    tokens = command.split()
    merged_tokens = []
    in_quotes = False
    current_token = []
    for token in tokens:
        if token.startswith('"') and token.endswith('"') and len(token) > 1:
            merged_tokens.append(token)
        elif token.startswith('"'):
            in_quotes = True
            current_token = [token[1:]]
        elif token.endswith('"'):
            current_token.append(token[:-1])
            merged_tokens.append(' '.join(current_token))
            in_quotes = False
        elif in_quotes:
            current_token.append(token)
        else:
            merged_tokens.append(token)
    return merged_tokens

class Mp2Client:
    user = None
    def __init__(self, config_filename):
        self.db_conn_params = read_config(filename=config_filename, section="postgresql")
        self.conn = None
        # Create guest user
        self.connect()
        try:
            cursor = self.conn.cursor()
            # Create a new guest user
            cursor.execute("INSERT INTO Users (current_query_count, max_query_limit) VALUES (0, 10000) RETURNING user_id")
            user_id = cursor.fetchone()[0]
            self.conn.commit()
            # Create User object
            self.user = User(user_id=str(user_id), current_query_count=0, max_query_limit=10000)
        except Exception:
            self.conn.rollback()
        finally:
            self.disconnect()
        
        
    """
        Connects to PostgreSQL database and returns connection object.
    """
    def connect(self):
        self.conn = psycopg2.connect(**self.db_conn_params)
        self.conn.autocommit = False

    """
        Disconnects from PostgreSQL database.
    """
    def disconnect(self):
        self.conn.close()

    """
        Prints list of available commands of the software.
    """
    def help(self):
        print("\n*** Geographic Information System ***")
        print("> help")
        print("> sign_up <admin_id> <password> <level_id>")
        print("> sign_in <admin_id> <password>")
        print("> sign_out")
        print("> show_levels")
        print("> show_my_level")
        print("> change_level <new_level_id>")
        print("> get_statistics <name> [<country_name>]")
        print("> update_religion <country_name> <religion_name1> <religion_name2> <percentage>")
        print("> transfer_city <city_name> <current_country> <new_country>")
        print("> adjust_population <name> [<country_name>] <new_population>")
        print("> quit")

    
    """
        Saves admin with given details.
        - Return type is a tuple, 1st element is a boolean and 2nd element is the response message from messages.py.
        - If the operation is successful, commit changes and return tuple (True, CMD_EXECUTION_SUCCESS).
        - If the admin_id already exists, return tuple (False, USERNAME_EXISTS).
        - If any exception occurs; rollback, do nothing on the database and return tuple (False, CMD_EXECUTION_FAILED).
    """
    def sign_up(self, admin_id, password, level_id):
        self.connect()
        try:
            # First check if the level_id exists
            cursor = self.conn.cursor()
            cursor.execute("SELECT level_id FROM AccessLevel WHERE level_id = %s", (level_id,))
            if cursor.fetchone() is None:
                return False, CMD_EXECUTION_FAILED
            
            # Check if admin_id already exists
            cursor.execute("SELECT admin_id FROM Administrator WHERE admin_id = %s", (admin_id,))
            if cursor.fetchone() is not None:
                return False, USERNAME_EXISTS
            
            # Insert new admin
            cursor.execute(
                "INSERT INTO Administrator (admin_id, password, session_count, level_id) VALUES (%s, %s, 0, %s)",
                (admin_id, password, level_id)
            )
            self.conn.commit()
            return True, CMD_EXECUTION_SUCCESS
        except Exception:
            self.conn.rollback()
            return False, CMD_EXECUTION_FAILED
        finally:
            self.disconnect()

    """
        Retrieves admin information if admin_id and password is correct and admin's session_count < max_parallel_sessions.
        - Return type is a tuple, 1st element is a Administrator object and 2nd element is the response message from messages.py.
        - If admin_id or password is wrong, return tuple (None, USER_SIGNIN_FAILED).
        - If session_count < max_parallel_sessions, commit changes (increment session_count) and return tuple (Administrator, CMD_EXECUTION_SUCCESS).
        - If session_count >= max_parallel_sessions, return tuple (None, USER_ALL_SESSIONS_ARE_USED).
        - If any exception occurs; rollback, do nothing on the database and return tuple (None, USER_SIGNIN_FAILED).
        - Do not forget the remove the guest user.
    """
    def sign_in(self, admin_id, password):
        # TODO: Implement this function
        return None, CMD_EXECUTION_FAILED


    """
        Signs out from given admin's account.
        - Return type is a tuple, 1st element is a boolean and 2nd element is the response message from messages.py.
        - Decrement session_count of the admin in the database.
        - If the operation is successful, commit changes and return tuple (True, CMD_EXECUTION_SUCCESS).
        - If no admin is account is signed in, return tuple (False, NO_ACTIVE_ADMIN).
        - If any exception occurs; rollback, do nothing on the database and return tuple (False, CMD_EXECUTION_FAILED).
        - Do not forget to recreate a guest user.
    """
    def sign_out(self, admin):
        # TODO: Implement this function
        return False, CMD_EXECUTION_FAILED


    """
        Quits from program.
        - Return type is a tuple, 1st element is a boolean and 2nd element is the response message from messages.py.
        - Remember to sign authenticated user/admin out first.
        - If the operation is successful, commit changes and return tuple (True, CMD_EXECUTION_SUCCESS).
        - If any exception occurs; rollback, do nothing on the database and return tuple (False, CMD_EXECUTION_FAILED).
        - If not authenticated, do not forget to remove the guest user.
    """
    def quit(self, admin):
        # TODO: Implement this function
        return False, CMD_EXECUTION_FAILED


    """
        Retrieves all available access levels and prints them.
        - Return type is a tuple, 1st element is a boolean and 2nd element is the response message from messages.py.
        - If the operation is successful; print available plans and return tuple (True, CMD_EXECUTION_SUCCESS).
        - If any exception occurs; return tuple (False, CMD_EXECUTION_FAILED).
        
        Output should be like:
        #|Name|Max Sessions
        1|Basic|2
        2|Advanced|5
        3|Premium|10
    """
    def show_levels(self):
        # TODO: Implement this function
        return False, CMD_EXECUTION_FAILED
    
    """
        Retrieves plan of the authenticated admin.
        - Return type is a tuple, 1st element is a boolean and 2nd element is the response message from messages.py.
        - If the operation is successful; print the admin's plan and return tuple (True, CMD_EXECUTION_SUCCESS).
        - If the admin is not signed in, return tuple (False, USER_NOT_AUTHORIZED).
        - If any other exception occurs; return tuple (False, CMD_EXECUTION_FAILED).
        
        Output should be like:
        #|Name|Max Sessions
        1|Basic|2
    """
    def show_my_level(self, admin):
        # TODO: Implement this function
        return False, CMD_EXECUTION_FAILED

    """
        Subscribe authenticated administrator to new plan.
        - Return type is a tuple, 1st element is a Administrator object and 2nd element is the response message from messages.py.
        - If the new_level_id is a downgrade; rollback, do nothing on the database and return tuple (None, DOWNGRADE_NOT_ALLOWED).
        - If the new_level_id is the same level; rollback, do nothing on the database and return tuple (None, SAMEGRADE_NOT_ALLOWED).
        - If the operation is successful, commit changes and return tuple (admin, CMD_EXECUTION_SUCCESS).
        - If any other exception occurs; rollback, do nothing on the database and return tuple (None, CMD_EXECUTION_FAILED).
    """
    def change_level(self, admin, new_level_id):
        # TODO: Implement this function
        return None, CMD_EXECUTION_FAILED

    """
        Retrieves statistics of the given city/country/continent.
        - Return type is a tuple, 1st element is a boolean and 2nd element is the response message from messages.py.
        - If the operation is successful; print the statistics and return tuple (True, CMD_EXECUTION_SUCCESS).
        - If the name is not unique and country_name is not given, return tuple (False, AMBIGUOUS_CITY).
        - If the name is not unique and country_name is given, return tuple (False, NO_ENTITY_FOUND).
        - If any other exception occurs; return tuple (False, CMD_EXECUTION_FAILED).
        - Do not forget the users table.
    """
    def get_statistics(self, name, country_name=None):
        # TODO: Implement this function
        return None, CMD_EXECUTION_FAILED

    """
        Updates the religion of the given country.
        - Return type is a tuple, 1st element is a boolean and 2nd element is the response message from messages.py.
        - If the operation is successful; commit changes and return tuple (True, CMD_EXECUTION_SUCCESS).
        - If the country_name is not found, return tuple (False, NO_ENTITY_FOUND).
        - If the religion_name2 is not found, return tuple (False, RELIGION_NOT_FOUND).
        - If the religion_name2 has insufficient percentage, return tuple (False, RELIGION_INSUFFICIENT_PERCENTAGE).
        - If the percentages would be out of 0-100, return tuple (False, INVALID_PERCENTAGE).
        - If the admin is not signed in, return tuple (False, USER_NOT_AUTHORIZED).
    """
    def update_religion(self, admin, country_name, religion_name1, religion_name2, percentage):
        # TODO: Implement this function
        return None, CMD_EXECUTION_FAILED


    """
        Transfers the city from current country to new country. follow the instructions in mp2.pdf
        - Return type is a tuple, 1st element is a boolean and 2nd element is the response message from messages.py.
        - If the operation is successful; commit changes and return tuple (True, CMD_EXECUTION_SUCCESS).
        - If the city with given current_country is not found, return tuple (False, NO_ENTITY_FOUND).
        - If the country with given new_country is not found, return tuple (False, MISSING_OCCUPIER_COUNTRY).
        - If both countries are the same, return tuple (False, SAME_COUNTRY).
        - If the admin is not signed in, return tuple (False, USER_NOT_AUTHORIZED).
    """
    def transfer_city(self, admin, city_name, current_country, new_country):  
        # TODO: Implement this function
        return None, CMD_EXECUTION_FAILED

    """
        Adjusts the population of the given city/country. follow the instructions in mp2.pdf
        - Return type is a tuple, 1st element is a boolean and 2nd element is the response message from messages.py.
        - If the operation is successful; commit changes and return tuple (True, CMD_EXECUTION_SUCCESS).
        - If the population is negative, return tuple (False, NO_NEGATIVE_POPULATION).
        - If the city/country with given name is not found, return tuple (False, NO_ENTITY_FOUND).
        - If the city name is not unique, return tuple (False, AMBIGUOUS_CITY).
        - If the admin is not signed in, return tuple (False, USER_NOT_AUTHORIZED).
    """
    def adjust_population(self, admin, name, country_name=None, new_population=None):
        # TODO: Implement this function
        return None, CMD_EXECUTION_FAILED


