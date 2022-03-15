def format_time(time: int, show_hours=False):
    
    hours = time // 3600
    minutes = (time - hours * 3600) // 60
    seconds = time % 60

    if show_hours:
        return f"{hours:02}:{minutes:02}:{seconds:02}"
    else:
        return f"{minutes:02}:{seconds:02}"

