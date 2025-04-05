class AudioEvent:
    def __init__(self, estacion, estado, timestamp, detalle, similarity):
        self.estacion = estacion
        self.estado = estado
        self.timestamp = timestamp
        self.detalle = detalle
        self.similarity = similarity

    def to_dict(self):
        return {
            "estacion": self.estacion,
            "estado": self.estado,
            "timestamp": self.timestamp,
            "detalle": self.detalle,
            "similarity": self.similarity
        }
