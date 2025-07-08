def id_generator(start: int = 0):
    current = start
    while True:
        yield current
        current += 1
