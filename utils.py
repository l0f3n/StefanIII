def format_time(time: int, hours_width=2):
    
    hours = time // 3600

    minutes = (time - hours * 3600) // 60
    
    seconds = time % 60

    return f"{str(hours).zfill(hours_width)}:{str(minutes).zfill(2)}:{str(seconds).zfill(2)}"

# print("0:   ", format_time(2000, 3))
# print("1:   ", format_time(3600, 3))
# print("23:  ", format_time(82800, 3))
# print("111: ", format_time(399666, 3))
