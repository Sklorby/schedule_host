def get_response(user_input: str) -> str:
    lowered: str = user_input.lower()
    
    if lowered == 'hello':
        return "hey there!"
    else:
        return "I don't get it"
    
