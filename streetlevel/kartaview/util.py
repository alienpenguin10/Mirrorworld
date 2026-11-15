# Mirrorworld addition (not in upstream streetlevel).
def build_permalink(sequence_id: int, sequence_index: int = 0) -> str:
    """
    Creates a link to a photo on kartaview.org.

    :param sequence_id: ID of the sequence (track) the photo belongs to.
    :param sequence_index: *(optional)* Position of the photo in the sequence. Defaults to 0.
    :return: A KartaView URL.
    """
    return f"https://kartaview.org/details/{sequence_id}/{sequence_index}/track-info"
