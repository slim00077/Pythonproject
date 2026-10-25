class BusinessRuleError(Exception):
    """Raised by domain services when an operation breaks a business rule.

    The message is written in French because views display it to the user.
    """

    def __init__(self, message):
        super().__init__(message)
        self.message = message
