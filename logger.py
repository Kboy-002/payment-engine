from datetime import datetime


def log_event(level, message, details=""):

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    log_line = f"{timestamp} | {level} | {message} | {details}\n"

    with open("system_logs.txt", "a", encoding="utf-8") as log_file:
        log_file.write(log_line)
