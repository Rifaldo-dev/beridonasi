user_states = {}

class UserState:
    @staticmethod
    def set(user_id, state, data=None):
        user_states[user_id] = {'state': state, 'data': data or {}}

    @staticmethod
    def get(user_id):
        return user_states.get(user_id, {'state': None, 'data': {}})

    @staticmethod
    def clear(user_id):
        if user_id in user_states:
            del user_states[user_id]

    @staticmethod
    def update_data(user_id, key, value):
        if user_id in user_states:
            user_states[user_id]['data'][key] = value

    @staticmethod
    def exists(user_id):
        return user_id in user_states
