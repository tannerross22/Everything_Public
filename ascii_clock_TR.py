##Tanner's Section##
    if clock_type == '12':
        hours, minutes = time.split(':')
        hours = int(hours)
        minutes = int(minutes)
        period = "AM" if hours < 12 else "PM"
        if hours == 0:
            hours = 12
        elif hours > 12:
            hours -= 12
        time = '{:d}:{:02d} {}'.format(hours, minutes, period)

    for i in range(5):
        line = ""
        for digit in time:
            if digit == ':':
                line += symbols[digit][i]
            elif digit in symbols:  # Check if the digit exists in the symbols dictionary
                line += symbols[digit][i].replace('*', character)
            else:
                line += ' ' * 3  # If digit not found, use spaces
            line += ' '  # Add space between digits and colon
        print(line)