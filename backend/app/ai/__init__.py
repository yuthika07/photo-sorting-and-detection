"""
AI package -- the computer vision pipeline.

Contents so far:
    face_detection/    -> SCRFD-based face detection (Phase 4). Locates
                           faces and returns bounding boxes, confidence
                           scores, and landmarks. Does NOT identify who
                           a face belongs to.
    face_recognition/    -> ArcFace-based face embedding (Phase 5). Turns
                             a detected face into a 512-d identity vector
                             and can store/retrieve it via the Phase 2
                             database layer. Does NOT cluster faces into
                             people.
    clustering/            -> DBSCAN-based face clustering (Phase 6). Groups
                               a batch of embeddings into "Person N" clusters,
                               explicitly separating out faces that don't
                               confidently belong to any group.

Still to come in later phases: perceptual hashing for duplicate
detection, and quality scoring -- per the AI Pipeline section of the
architecture document.
"""
