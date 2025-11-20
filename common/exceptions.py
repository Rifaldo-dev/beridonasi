class BotException(Exception):
    pass

class BanException(BotException):
    pass

class PendingDonationException(BotException):
    pass

class InvalidAmountException(BotException):
    pass

class QRISException(BotException):
    pass

class DatabaseException(BotException):
    pass

class AdminException(BotException):
    pass
