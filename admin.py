class Administrator:
    def __init__(self, admin_id="", session_count=0, plan_id=0):
        self.admin_id = admin_id
        self.session_count = session_count
        self.plan_id = plan_id

    def __str__(self):
        return self.admin_id

class User:
    def __init__(self, user_id="", current_query_count=0, max_query_limit=10000):
        self.user_id = user_id
        self.current_query_count = current_query_count
        self.max_query_limit = max_query_limit

    def __str__(self):
        return self.user_id
