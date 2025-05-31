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
        # TODO: Implement this function(bind guest user)

        # creating guest user in beginning
        self.connect()

        try:
            query_ex = self.conn.cursor()

            # inserting new guest user into the users table
            query_ex.execute("INSERT INTO users (current_query_count, max_query_limit) VALUES (0, 10000) RETURNING user_id")
            
            user_id = query_ex.fetchone()[0]
            self.conn.commit()

            # creating user object
            self.user = User(user_id=str(user_id), current_query_count=0, max_query_limit=10000)
            
            #debug 
            #print(f"guest user created with id: {user_id}")
            self.disconnect()

        except:
            self.conn.rollback()
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

    #todo
    def sign_up(self, admin_id, password, level_id):
        # TODO: Implement this function

        self.connect()

        try:
            query_ex = self.conn.cursor()

            # checking if level exist
            query_ex.execute("SELECT level_id FROM accesslevels WHERE level_id = %s", (level_id,))

            # if level does not exist, return False
            if query_ex.fetchone() is None:
                self.disconnect()
                return False, CMD_EXECUTION_FAILED
            
            # checking if admin already exists
            query_ex.execute("SELECT admin_id FROM administrators WHERE admin_id = %s", (admin_id,))

            # if admin_id exists, return False, username exists
            if query_ex.fetchone() is not None:
                self.disconnect()
                return False, USERNAME_EXISTS
            
            # insert new admin
            query_ex.execute(
                "INSERT INTO administrators (admin_id, password, session_count, level_id) VALUES (%s, %s, 0, %s)",
                (admin_id, password, level_id)
            )

            # commit changes
            self.conn.commit()
            self.disconnect()
            return True, CMD_EXECUTION_SUCCESS
        
        except:
            self.conn.rollback()
            self.disconnect()
            return False, CMD_EXECUTION_FAILED
        


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

        self.connect()

        try:
            query_ex = self.conn.cursor()
            

            # if admin_id exists
            query_ex.execute("SELECT admin_id, password, level_id FROM administrators WHERE admin_id = %s", (admin_id,))
            
            admin_row = query_ex.fetchone()
            
            # if admin_id does not exist, return None
            if admin_row is None:
                self.disconnect()
                return None, USER_SIGNIN_FAILED
            
            # if password matches
            if admin_row[1] != password:
                self.disconnect()
                return None, USER_SIGNIN_FAILED
            
            # if level exists
            query_ex.execute("SELECT * FROM accesslevels WHERE level_id = %s", (admin_row[2],))

            level_row = query_ex.fetchone()
            
            if level_row is None:
                self.disconnect()
                return None, USER_SIGNIN_FAILED
            
            # select admin data, session count and max parallel sessions
            query = """
                SELECT a.admin_id, a.level_id, a.session_count, l.max_parallel_sessions 
                FROM administrators a
                JOIN accesslevels l ON a.level_id = l.level_id
                WHERE a.admin_id = %s AND a.password = %s
            """
            query_ex.execute(query, (admin_id, password))
            admin_data = query_ex.fetchone()
            
            # if no admin data found, return none
            if admin_data is None:
                self.disconnect()
                return None, USER_SIGNIN_FAILED
            
            # 
            admin_id, level_id, session_count, max_sessions = admin_data
            
            # check if session count is less than max sessions
            if session_count >= max_sessions:
                self.disconnect()
                return None, USER_ALL_SESSIONS_ARE_USED
            
            # increment session count atomically
            query_ex.execute("""
                UPDATE administrators 
                SET session_count = session_count + 1 
                WHERE admin_id = %s
            """, (admin_id,))
            
            # removing guest user if exists
            if self.user is not None:
                user_id = self.user.user_id
                query_ex.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
                self.user = None
    
            # create Administrator object
            admin = Administrator(admin_id, level_id)
            
            self.conn.commit()
            self.disconnect()
            return admin, CMD_EXECUTION_SUCCESS
            

        except:
            self.conn.rollback()
            self.disconnect()
            return None, USER_SIGNIN_FAILED




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

        self.connect()

        try:
            
            #check if admin is signed in
            if admin is None:
                self.disconnect()
                return False, NO_ACTIVE_ADMIN
            
            query_ex = self.conn.cursor()
            
            # decrease session count atomically, cant be less than 0
            query_ex.execute("""
                UPDATE administrators 
                SET session_count = GREATEST(0, session_count - 1)
                WHERE admin_id = %s
            """, (admin.admin_id,))
            
            # create new guest user
            query_ex.execute("INSERT INTO users (current_query_count, max_query_limit) VALUES (0, 10000) RETURNING user_id")
            user_id = query_ex.fetchone()[0]
            
            # create User object
            self.user = User(user_id=str(user_id), current_query_count=0, max_query_limit=10000)
            
            self.conn.commit()
            self.disconnect()
            return True, CMD_EXECUTION_SUCCESS
            
        except:
            self.conn.rollback()
            self.disconnect()
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

        self.connect()

        try:

            query_ex = self.conn.cursor()
            
            # if admin is signed in, decrement session count, sign out
            if admin is not None:
                query_ex.execute("""
                    UPDATE administrators 
                    SET session_count = GREATEST(0, session_count - 1)
                    WHERE admin_id = %s
                """, (admin.admin_id,))
            
            # remove guest user if exists
            if self.user is not None:
                query_ex.execute("DELETE FROM users WHERE user_id = %s", (self.user.user_id,))
                self.user = None
                
            self.conn.commit()
            self.disconnect()
            return True, CMD_EXECUTION_SUCCESS
            
        except:
            self.conn.rollback()
            self.disconnect()
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

    # pdf and the commented output style is different, i use the pdf style output as stated in forum
    def show_levels(self):
        # TODO: Implement this function

        self.connect()

        try:

            query_ex = self.conn.cursor()

            # show all access levels
            query_ex.execute("SELECT * FROM accesslevels")
            levels = query_ex.fetchall()
            
            print("ID|Level Name|Max Sessions")
            for level in levels:
                print(f"{level[0]}|{level[1]}|{level[2]}")
                
            
            self.disconnect()
            return True, CMD_EXECUTION_SUCCESS
            
        except:
            self.disconnect()
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

        # if an admin is not signed in, return False
        if admin is None:
            return False, USER_NOT_AUTHORIZED
    
        self.connect()

        try:

            query_ex = self.conn.cursor()
            
            # get admin level information
            query_ex.execute("""
                SELECT a.level_id, al.name, al.max_parallel_sessions
                FROM administrators a
                JOIN accesslevels al ON a.level_id = al.level_id
                WHERE a.admin_id = %s
            """, (admin.admin_id,))
            
            level_info = query_ex.fetchone()
            
            # if level_info is None, return False
            if level_info is None:
                self.disconnect()
                return False, CMD_EXECUTION_FAILED
            
            # print admin level information in pdf format
            print("ID|Level Name|Max Sessions")
            print(f"{level_info[0]}|{level_info[1]}|{level_info[2]}")
            
            self.disconnect()
            return True, CMD_EXECUTION_SUCCESS
            
        except:
            self.disconnect()
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

        # if an admin is not signed in, return None
        if admin is None:
            return None, USER_NOT_AUTHORIZED
    
        self.connect()

        try:

            query_ex = self.conn.cursor()
            
            # check if new_level_id exists
            query_ex.execute("SELECT level_id, max_parallel_sessions FROM accesslevels WHERE level_id = %s", (new_level_id,))
            new_level = query_ex.fetchone()
            
            # if new_level_id does not exist, return None
            if new_level is None:
                self.disconnect()
                return None, CMD_EXECUTION_FAILED
            
            # get admin information
            query_ex.execute("""
                SELECT a.level_id, a.session_count, al.max_parallel_sessions
                FROM administrators a
                JOIN accesslevels al ON a.level_id = al.level_id
                WHERE a.admin_id = %s
            """, (admin.admin_id,))
            
            current_info = query_ex.fetchone()
            
            # if current_info is None, return None
            if current_info is None:
                self.disconnect()
                return None, CMD_EXECUTION_FAILED
            
            current_level_id, session_count, current_max_sessions = current_info
            new_max_sessions = new_level[1]
            
            # if new_level_id is the same as current level_id, return None
            if current_level_id == new_level_id:
                self.disconnect()
                return None, SAMEGRADE_NOT_ALLOWED
            
            # if new_level_id is a downgrade
            if new_max_sessions <= current_max_sessions:
                self.disconnect()
                return None, DOWNGRADE_NOT_ALLOWED
            
            # if multiple sessions are active
            if session_count > 1:
                self.disconnect()
                return None, CMD_EXECUTION_FAILED
            
            # if the new level is valid, update admin level_id
            query_ex.execute("""
                UPDATE administrators 
                SET level_id = %s
                WHERE admin_id = %s
            """, (new_level_id, admin.admin_id))
            

            admin.level_id = new_level_id
            
            self.conn.commit()
            self.disconnect()
            return admin, CMD_EXECUTION_SUCCESS
        
        except:
            self.conn.rollback()
            self.disconnect()
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

        self.connect()

        try:
            query_ex = self.conn.cursor()
            
            # guest user session active
            # admin is not signed in, so user is None
            if self.user is not None:

                # check query limit
                if self.user.current_query_count > 10000:
                    print("10000 query limit reached.")
                    self.conn.commit()
                    self.disconnect()
                    return False, CMD_EXECUTION_FAILED
                
                # increment user query count
                query_ex.execute("""
                    UPDATE users 
                    SET current_query_count = current_query_count + 1 
                    WHERE user_id = %s
                """, (self.user.user_id,))
                self.user.current_query_count += 1
            
            # checking if name is a continent
            query_ex.execute("SELECT name, area FROM continent WHERE name ILIKE %s", (name,))
            continent_result = query_ex.fetchone()
            
            if continent_result:
                # Displays: Name, Country Count (≤50% encompassed)
                query_ex.execute("""
                    SELECT COUNT(*) 
                    FROM encompasses 
                    WHERE continent ILIKE %s AND percentage > 50
                """, (name,))
                country_count = query_ex.fetchone()[0]
                
                print("TYPE|NAME|COUNTRIES")
                print(f"Continent|{continent_result[0]}|{country_count}")
                
                self.conn.commit()
                self.disconnect()
                return True, CMD_EXECUTION_SUCCESS
            


            # checking if the name is a country
            query_ex.execute("SELECT name, population FROM country WHERE name ILIKE %s", (name,))
            country_result = query_ex.fetchone()
            
            if country_result:
                country_name_found = country_result[0]
                population = country_result[1]

                # Displays: Name, Population, GDP, Top Language, Top Religion
                
                # gdp
                query_ex.execute("""
                    SELECT gdp
                    FROM economy 
                    WHERE country = (SELECT code FROM country WHERE name ILIKE %s)
                """, (name,))
                economy_data = query_ex.fetchone()
                
                gdp = economy_data[0] if economy_data else "N/A"
                

                # top language
                query_ex.execute("""
                    SELECT language, percentage 
                    FROM spoken 
                    WHERE country = (SELECT code FROM country WHERE name ILIKE %s)
                    ORDER BY percentage DESC 
                    LIMIT 1
                """, (name,))
                top_language = query_ex.fetchone()
                top_lang_str = f"{top_language[0]} ({top_language[1]}%)" if top_language else "N/A"
                

                # top religion
                query_ex.execute("""
                    SELECT name, percentage 
                    FROM religion 
                    WHERE country = (SELECT code FROM country WHERE name ILIKE %s)
                    ORDER BY percentage DESC 
                    LIMIT 1
                """, (name,))
                top_religion = query_ex.fetchone()
                top_rel_str = f"{top_religion[0]} ({top_religion[1]}%)" if top_religion else "N/A"
                
                print("TYPE|NAME|POPULATION|GDP|TOP_LANGUAGE|TOP_RELIGION")
                print(f"Country|{country_name_found}|{population:,}|${gdp}|{top_lang_str}|{top_rel_str}")
                
                self.conn.commit()
                self.disconnect()
                return True, CMD_EXECUTION_SUCCESS
            

            # checking if name is a city
            if country_name is None:

                #Displays: Name, Population, Elevation

                # check city without country
                query_ex.execute("SELECT COUNT(*) FROM city WHERE name ILIKE %s", (name,))
                city_count = query_ex.fetchone()[0]
                
                if city_count > 1:
                    self.conn.commit()
                    self.disconnect()
                    return False, AMBIGUOUS_CITY
                elif city_count == 0:
                    self.conn.commit()
                    self.disconnect()
                    return False, NO_ENTITY_FOUND
                
                # unique city found
                query_ex.execute("""
                    SELECT c.name, c.population, c.elevation, co.name as country_name
                    FROM city c
                    JOIN country co ON c.country = co.code
                    WHERE c.name ILIKE %s
                """, (name,))
                city_result = query_ex.fetchone()
                
                if city_result:
                    print("TYPE|NAME|POPULATION|ELEVATION")
                    print(f"City|{city_result[0]}|{city_result[1]:,}|{city_result[2]}m")
                    
                    self.conn.commit()
                    self.disconnect()
                    return True, CMD_EXECUTION_SUCCESS
                
            else:
                # check city with country
                query_ex.execute("""
                    SELECT c.name, c.population, c.elevation, co.name as country_name
                    FROM city c
                    JOIN country co ON c.country = co.code
                    WHERE c.name ILIKE %s AND co.name ILIKE %s
                """, (name, country_name))
                city_result = query_ex.fetchone()
                
                if city_result:
                    print("TYPE|NAME|COUNTRY|POPULATION|ELEVATION")
                    print(f"City|{city_result[0]}|{city_result[3]}|{city_result[1]:,}|{city_result[2]}m")
                    
                    self.conn.commit()
                    self.disconnect()
                    return True, CMD_EXECUTION_SUCCESS
                else:
                    self.conn.commit()
                    self.disconnect()
                    return False, NO_ENTITY_FOUND
            
            # if no entity found
            self.conn.commit()
            self.disconnect()
            return False, NO_ENTITY_FOUND
            
        except:
            self.conn.rollback()
            self.disconnect()
            return False, CMD_EXECUTION_FAILED



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
        

        # check if admin is signed in
        if admin is None:
            return False, USER_NOT_AUTHORIZED
        
        self.connect()
        
        try:
            query_ex = self.conn.cursor()
            
            # validate percentage is between 0-100
            percentage = float(percentage)
            if percentage < 0 or percentage > 100:
                self.disconnect()
                return False, INVALID_PERCENTAGE
            
            # check if country exists and get country code
            query_ex.execute("SELECT code FROM country WHERE name ILIKE %s", (country_name,))
            country_result = query_ex.fetchone()
            
            # if country does not exist, return False
            if country_result is None:
                self.disconnect()
                return False, NO_ENTITY_FOUND
            
            country_code = country_result[0]
            
            # check if religion_name2 exists for this country
            query_ex.execute("""
                SELECT name, percentage 
                FROM religion 
                WHERE country = %s AND name ILIKE %s
            """, (country_code, religion_name2))
            religion2_result = query_ex.fetchone()
            
            # if religion2 does not exist, return False
            if religion2_result is None:
                self.disconnect()
                return False, RELIGION_NOT_FOUND
            
            current_religion2_percentage = float(religion2_result[1])
            
            # check if religion2 has sufficient percentage
            if current_religion2_percentage < percentage:
                self.disconnect()
                return False, RELIGION_INSUFFICIENT_PERCENTAGE
            
            # check if religion_name1 exists for this country
            query_ex.execute("""
                SELECT name, percentage 
                FROM religion 
                WHERE country = %s AND name ILIKE %s
            """, (country_code, religion_name1))
            religion1_result = query_ex.fetchone()
            
            # calculate new percentages
            new_religion2_percentage = current_religion2_percentage - percentage
            
            if religion1_result is None:
                # religion1 does not exist, create new entry
                new_religion1_percentage = percentage
                
                query_ex.execute("""
                    INSERT INTO religion (country, name, percentage) 
                    VALUES (%s, %s, %s)
                """, (country_code, religion_name1, new_religion1_percentage))

            else:
                # religion1 exists, update percentage
                current_religion1_percentage = float(religion1_result[1])
                new_religion1_percentage = current_religion1_percentage + percentage
                
                # validate new percentage is not over 100
                if new_religion1_percentage > 100:
                    self.disconnect()
                    return False, INVALID_PERCENTAGE
                
                query_ex.execute("""
                    UPDATE religion 
                    SET percentage = %s 
                    WHERE country = %s AND name ILIKE %s
                """, (new_religion1_percentage, country_code, religion_name1))
            
            # update or remove religion2
            if new_religion2_percentage == 0:
                # remove religion2 if percentage becomes 0
                query_ex.execute("""
                    DELETE FROM religion 
                    WHERE country = %s AND name ILIKE %s
                """, (country_code, religion_name2))

            else:
                # update religion2 percentage
                query_ex.execute("""
                    UPDATE religion 
                    SET percentage = %s 
                    WHERE country = %s AND name ILIKE %s
                """, (new_religion2_percentage, country_code, religion_name2))
            
            # print success message
            print("RELIGION|PERCENTAGE")
            print(f"{religion_name1}|{new_religion1_percentage}% (+{percentage})")
            
            if new_religion2_percentage > 0:
                print(f"{religion_name2}|{new_religion2_percentage}% (-{percentage})")
                
            else:
                print(f"{religion_name2}|0% (-{percentage}) [REMOVED]")
            
            self.conn.commit()
            self.disconnect()
            return True, CMD_EXECUTION_SUCCESS
            
        except:
            self.conn.rollback()
            self.disconnect()
            return False, CMD_EXECUTION_FAILED


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
        
        
        # check if admin is signed in
        if admin is None:
            return False, USER_NOT_AUTHORIZED
        
        # check if both countries are the same
        if current_country.lower() == new_country.lower():
            return False, SAME_COUNTRY
        
        self.connect()
        
        try:
            query_ex = self.conn.cursor()
            
            # get current country code
            query_ex.execute("SELECT code, name FROM country WHERE name ILIKE %s", (current_country,))
            current_result = query_ex.fetchone()

            # if current country does not exist, return False
            if current_result is None:
                self.disconnect()
                return False, NO_ENTITY_FOUND
            
            current_code, current_name = current_result
            
            # get new country code  
            query_ex.execute("SELECT code FROM country WHERE name ILIKE %s", (new_country,))
            new_result = query_ex.fetchone()

            # if new country does not exist, return False
            if new_result is None:
                self.disconnect()
                return False, MISSING_OCCUPIER_COUNTRY
            
            new_code = new_result[0]
            
            # check if city exists in current country
            query_ex.execute("SELECT name FROM city WHERE name ILIKE %s AND country = %s", 
                        (city_name, current_code))
            
            city_result = query_ex.fetchone()

            # if city does not exist in current country, return False
            if city_result is None:
                self.disconnect()
                return False, NO_ENTITY_FOUND
            
            # check if city is capital
            query_ex.execute("SELECT capital FROM country WHERE code = %s", (current_code,))
            capital_result = query_ex.fetchone()

            is_capital = capital_result and capital_result[0] and capital_result[0].lower() == city_name.lower()
            
            # transfer city
            query_ex.execute("UPDATE city SET country = %s WHERE name ILIKE %s AND country = %s", 
                           (new_code, city_name, current_code))
            
            # capital handling
            if is_capital:
                query_ex.execute("SELECT name FROM city WHERE country = %s ORDER BY name LIMIT 1", 
                            (current_code,))
                
                new_capital = query_ex.fetchone()

                # if there are no cities left in the current country, set capital to NULL
                if new_capital:
                    query_ex.execute("UPDATE country SET capital = %s WHERE code = %s", 
                                (new_capital[0], current_code))
                    
                else:
                    query_ex.execute("UPDATE country SET capital = NULL WHERE code = %s", 
                                (current_code,))
            
            # check if country should be removed
            query_ex.execute("SELECT COUNT(*) FROM city WHERE country = %s", (current_code,))
            remaining_cities = query_ex.fetchone()[0]
            
            if remaining_cities == 0:
                # remove from all existing tables
                query_ex.execute("DELETE FROM encompasses WHERE country = %s", (current_code,))
                query_ex.execute("DELETE FROM economy WHERE country = %s", (current_code,))
                query_ex.execute("DELETE FROM religion WHERE country = %s", (current_code,))
                query_ex.execute("DELETE FROM spoken WHERE country = %s", (current_code,))
                query_ex.execute("DELETE FROM country WHERE code = %s", (current_code,))
                print(f"Notice: Country named {current_name} has been removed.")
            
            self.conn.commit()
            self.disconnect()
            return True, CMD_EXECUTION_SUCCESS
            
        except:
            self.conn.rollback()
            self.disconnect()
            return False, CMD_EXECUTION_FAILED




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
        
        if admin is None:
            return False, USER_NOT_AUTHORIZED
    
        self.connect()
        
        try:
            query_ex = self.conn.cursor()
            
            # convert new_population to integer and validate
            new_population = int(new_population)

            # if new_population is negative, error
            if new_population < 0:
                self.disconnect()
                return False, NO_NEGATIVE_POPULATION
            
            # check if name is a country first
            query_ex.execute("SELECT code, name FROM country WHERE name ILIKE %s", (name,))
            country_result = query_ex.fetchone()
            
            if country_result:
                # update country population
                query_ex.execute("UPDATE country SET population = %s WHERE name ILIKE %s", 
                            (new_population, name))
                
                self.conn.commit()
                self.disconnect()
                return True, CMD_EXECUTION_SUCCESS
            
            # check if name is a city
            if country_name is None:
                # check city without country specification
                query_ex.execute("SELECT COUNT(*) FROM city WHERE name ILIKE %s", (name,))
                city_count = query_ex.fetchone()[0]
                
                # if city_count > 1, ambiguous city
                if city_count > 1:
                    self.disconnect()
                    return False, AMBIGUOUS_CITY
                
                # if city_count == 0, no entity found
                elif city_count == 0:
                    self.disconnect()
                    return False, NO_ENTITY_FOUND
                
                # unique city found, update population
                query_ex.execute("UPDATE city SET population = %s WHERE name ILIKE %s", 
                            (new_population, name))
                
            else:
                # check city with country specification
                query_ex.execute("""
                    SELECT c.name 
                    FROM city c
                    JOIN country co ON c.country = co.code
                    WHERE c.name ILIKE %s AND co.name ILIKE %s
                """, (name, country_name))

                city_result = query_ex.fetchone()
                
                # if no city found, return False
                if city_result is None:
                    self.disconnect()
                    return False, NO_ENTITY_FOUND
                
                # update city population with country specification
                query_ex.execute("""
                    UPDATE city 
                    SET population = %s 
                    WHERE name ILIKE %s AND country = (
                        SELECT code FROM country WHERE name ILIKE %s
                    )
                """, (new_population, name, country_name))
            
            self.conn.commit()
            self.disconnect()
            return True, CMD_EXECUTION_SUCCESS
            
        except:
            self.conn.rollback()
            self.disconnect()
            return False, CMD_EXECUTION_FAILED