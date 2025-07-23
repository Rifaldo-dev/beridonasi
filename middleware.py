
# Dictionary untuk menyimpan state user
user_states = {}

def set_user_state(user_id, state, data=None):
    """Set user state"""
    user_states[user_id] = {'state': state, 'data': data or {}}

def get_user_state(user_id):
    """Get user state"""
    return user_states.get(user_id, {'state': 'idle', 'data': {}})

def clear_user_state(user_id):
    """Clear user state"""
    if user_id in user_states:
        del user_states[user_id]
