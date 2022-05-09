class Track(object):

    def __init__(self, top_kante_uuid, top_kanten_track_counter):
        self.top_kante_uuid = top_kante_uuid
        self.id = f"{top_kante_uuid[-5:]}-{top_kanten_track_counter}"
        self.re_id = self.id + "-re"
        self.top_kante_length = 0
        self.left_point = None
        self.right_point = None
        self.geo_kanten = []
        self.signals = None
        self.shape_coordinates = []

    def set_top_kante_length(self, length):
        self.top_kante_length = length

    def set_left_point(self, left_point):
        self.left_point = left_point

    def set_right_point(self, right_point):
        self.right_point = right_point

    def set_geo_kanten(self, geo_kanten):
        self.geo_kanten = geo_kanten

    def set_signals(self, signals):
        self.signals = signals

    def add_shape_coordinates(self, new_coordinates):
        self.shape_coordinates.append(new_coordinates)
