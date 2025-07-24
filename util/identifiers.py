def id_generator(start: int = 0):
    """
    Generator of unique integer IDs. IDs are sequential and start at 0.
    """
    current = start
    while True:
        yield current
        current += 1
