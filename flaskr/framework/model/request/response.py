class Response(dict):
    def __init__(self, success: bool = False, message: str = '', name: str = '', info: dict = {}):
        self.message = message
        self.success = success
        self.name = name
        self.info = info
        super().__init__(self, message=message, success=success)

    def get_message(self) -> str:
        return self.message

    def is_success(self) -> bool:
        return self.success

    def get_name(self) -> str:
        return self.name

    def get_info(self) -> dict:
        return self.info
