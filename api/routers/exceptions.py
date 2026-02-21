class UserMessageError(Exception):
    def __init__(self, response_code, user_msg=None, server_msg=None):
        self.user_msg = user_msg or ""
        self.server_msg = server_msg or self.user_msg
        self.response_code = response_code
        super().__init__()
