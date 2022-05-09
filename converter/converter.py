import json
import math
import uuid

from planprorunningtrackgenerator import generator

from .model import Point, Track, RunningTrack, Signal
from .planprohelper import PlanProHelper
from .sumohelper import SUMOHelper


class Converter(object):

    def __init__(self, plan_pro_file_name):
        self.plan_pro_file_name = plan_pro_file_name

        self.points = dict()
        self.tracks = dict()
        self.running_tracks = dict()
        self.signals = dict()
        self.generate_running_tracks = True

        self.plan_pro_helper = PlanProHelper(plan_pro_file_name)
        self.number_of_fachdaten = self.plan_pro_helper.get_number_of_fachdaten()

    def convert(self):
        self.get_points()
        self.get_tracks()
        self.get_signals()
        self.get_running_tracks()

    def get_points(self):
        if len(self.points) == 0:
            for id_of_fachdaten in range(0, self.number_of_fachdaten):
                container = self.plan_pro_helper.get_container_by_fachdaten_id(id_of_fachdaten)

                for top_knoten in container.TOP_Knoten:
                    top_knoten_uuid = top_knoten.Identitaet.Wert
                    geo_knoten_uuid = top_knoten.ID_GEO_Knoten.Wert
                    point_obj = Point(top_knoten_uuid, geo_knoten_uuid)

                    x, y = self.plan_pro_helper.get_coordinates_of_geo_knoten(container, geo_knoten_uuid)
                    point_obj.set_coordinates(x, y)
                    self.points[top_knoten_uuid] = point_obj
        return self.points

    def get_tracks(self):
        if len(self.tracks) == 0:
            for id_of_fachdaten in range(0, self.number_of_fachdaten):
                container = self.plan_pro_helper.get_container_by_fachdaten_id(id_of_fachdaten)

                for top_kante in container.TOP_Kante:
                    top_kante_uuid = top_kante.Identitaet.Wert
                    point_a = self.points[top_kante.ID_TOP_Knoten_A.Wert]
                    point_b = self.points[top_kante.ID_TOP_Knoten_B.Wert]

                    tracks_in_order = []

                    # Signal
                    signals = self.plan_pro_helper.find_signals_at_top_kante(top_kante_uuid)
                    signal_list = []
                    for signal in signals:
                        sig_id = signal.Bezeichnung.Bezeichnung_Tabelle.Wert
                        signal_obj = Signal(signal.Identitaet.Wert,
                                            signal.Punkt_Objekt_TOP_Kante[0].ID_TOP_Kante.Wert,
                                            sig_id)
                        signal_obj.distance_from_start = float(signal.Punkt_Objekt_TOP_Kante[0].Abstand.Wert)
                        signal_obj.kind = signal.Signal_Real.Signal_Real_Aktiv.Signal_Funktion.Wert
                        signal_obj.wirkrichtung = signal.Punkt_Objekt_TOP_Kante[0].Wirkrichtung.Wert
                        signal_obj.top_kante_length = top_kante.TOP_Kante_Allg.TOP_Laenge.Wert
                        signal_list.append(signal_obj)
                    signal_list.sort(key=lambda sig: sig.distance_from_start, reverse=False)

                    # Get Shape
                    geo_kanten = self.plan_pro_helper.find_geo_kanten_by_top_kante_uuid(container, top_kante_uuid)
                    geo_kanten_in_order = []

                    first_edge = None
                    for geo_kante in geo_kanten:
                        if geo_kante.ID_GEO_Knoten_A.Wert == point_a.geo_knoten_uuid or geo_kante.ID_GEO_Knoten_B.Wert == point_a.geo_knoten_uuid:
                            first_edge = geo_kante
                            break
                    geo_kanten_in_order.append(first_edge)

                    second_last_node_uuid = point_a.geo_knoten_uuid
                    last_node_uuid = None
                    if first_edge.ID_GEO_Knoten_A.Wert == second_last_node_uuid:
                        last_node_uuid = first_edge.ID_GEO_Knoten_B.Wert
                    else:
                        last_node_uuid = first_edge.ID_GEO_Knoten_A.Wert

                    def get_next_edge(_last_node_uuid, _second_last_node):
                        for _geo_kante in geo_kanten:
                            if _geo_kante.ID_GEO_Knoten_A.Wert == _last_node_uuid or _geo_kante.ID_GEO_Knoten_B.Wert == _last_node_uuid:
                                if _geo_kante.ID_GEO_Knoten_A.Wert != _second_last_node and _geo_kante.ID_GEO_Knoten_B.Wert != _second_last_node:
                                    return _geo_kante
                        return None

                    cur_track_top_kanten_counter = 0
                    cur_track_obj = Track(top_kante_uuid, cur_track_top_kanten_counter)
                    cur_track_obj.left_point = point_a
                    x, y = self.plan_pro_helper.get_coordinates_of_geo_knoten(container, point_a.geo_knoten_uuid)
                    cur_track_obj.add_shape_coordinates(f"{x},{y}")
                    cur_track_obj.set_top_kante_length(top_kante.TOP_Kante_Allg.TOP_Laenge.Wert)
                    tracks_in_order.append(cur_track_obj)

                    # Go over all edges in order
                    next_edge = first_edge
                    edge_distance_sum_so_far = 0
                    processed_signals = []
                    while next_edge is not None:
                        # process signals
                        edge_length = float(next_edge.GEO_Kante_Allg.GEO_Laenge.Wert)
                        cur_track_obj.geo_kanten.append(next_edge)
                        for cur_signal in signal_list:
                            if cur_signal.id not in processed_signals and \
                               cur_signal.distance_from_start < edge_distance_sum_so_far + edge_length:
                                id_geo_knoten1 = next_edge.ID_GEO_Knoten_A.Wert
                                id_geo_knoten2 = next_edge.ID_GEO_Knoten_B.Wert
                                x1, y1 = self.plan_pro_helper.get_coordinates_of_geo_knoten(container, id_geo_knoten1)
                                x2, y2 = self.plan_pro_helper.get_coordinates_of_geo_knoten(container, id_geo_knoten2)
                                xdiff = x2 - x1
                                ydiff = y2 - y1
                                calc_len_of_geo_kante = math.sqrt((xdiff * xdiff) + (ydiff * ydiff))
                                calc_distance = (cur_signal.distance_from_start - edge_distance_sum_so_far) * \
                                                (calc_len_of_geo_kante / edge_length)
                                factor = calc_distance / calc_len_of_geo_kante
                                cur_signal.x = x1 + (factor * (x2 - x1))
                                cur_signal.y = y1 + (factor * (y2 - y1))

                                cur_signal.left_track = cur_track_obj
                                cur_track_obj.right_point = cur_signal
                                cur_track_obj.add_shape_coordinates(f"{cur_signal.x},{cur_signal.y}")

                                # Create new track
                                cur_track_top_kanten_counter = cur_track_top_kanten_counter + 1
                                cur_track_obj = Track(top_kante_uuid, cur_track_top_kanten_counter)
                                cur_track_obj.add_shape_coordinates(f"{cur_signal.x},{cur_signal.y}")
                                cur_track_obj.set_top_kante_length(top_kante.TOP_Kante_Allg.TOP_Laenge.Wert)
                                tracks_in_order.append(cur_track_obj)
                                cur_signal.right_track = cur_track_obj
                                cur_track_obj.left_point = cur_signal

                                self.signals[cur_signal.signal_uuid] = cur_signal
                                processed_signals.append(cur_signal.id)

                        x, y = self.plan_pro_helper.get_coordinates_of_geo_knoten(container, last_node_uuid)
                        cur_track_obj.add_shape_coordinates(f"{x},{y}")

                        edge_distance_sum_so_far = edge_distance_sum_so_far + edge_length
                        next_edge = get_next_edge(last_node_uuid, second_last_node_uuid)
                        if next_edge is not None:
                            second_last_node_uuid = last_node_uuid
                            if next_edge.ID_GEO_Knoten_A.Wert == second_last_node_uuid:
                                last_node_uuid = next_edge.ID_GEO_Knoten_B.Wert
                            else:
                                last_node_uuid = next_edge.ID_GEO_Knoten_A.Wert

                    cur_track_obj.right_point = point_b

                    # Anschluss A
                    anschluss_a = top_kante.TOP_Kante_Allg.TOP_Anschluss_A.Wert
                    if anschluss_a == "Ende" or anschluss_a == "Spitze":
                        point_a.set_head_edge(tracks_in_order[0])
                    elif anschluss_a == "Links":
                        point_a.set_left_edge(tracks_in_order[0])
                    elif anschluss_a == "Rechts":
                        point_a.set_right_edge_(tracks_in_order[0])

                    # Anschluss B
                    anschluss_b = top_kante.TOP_Kante_Allg.TOP_Anschluss_B.Wert
                    if anschluss_b == "Ende" or anschluss_b == "Spitze":
                        point_b.set_head_edge(tracks_in_order[-1])
                    elif anschluss_b == "Links":
                        point_b.set_left_edge(tracks_in_order[-1])
                    elif anschluss_b == "Rechts":
                        point_b.set_right_edge_(tracks_in_order[-1])

                    self.tracks[top_kante_uuid] = tracks_in_order
        return self.tracks

    def get_signals(self):
        if len(self.signals) == 0:
            self.get_tracks()  # while getting the tracks, the signals will read
        return self.signals

    def get_running_tracks(self, generate_running_tracks=False):
        if self.generate_running_tracks == generate_running_tracks and len(self.running_tracks) > 0:
            return self.running_tracks

        self.generate_running_tracks = generate_running_tracks

        def process_running_track(_fahrweg_uuid, _start_signal_uuid, _end_signal_uuid, _all_top_kanten_uuids):
            _fahrweg_obj = RunningTrack(_fahrweg_uuid)

            if _start_signal_uuid not in self.signals:
                return None  # Start signal type is so far not supported

            if _end_signal_uuid not in self.signals:
                return None  # End signal type is so far not supported

            _start_signal = self.signals[_start_signal_uuid]
            _fahrweg_obj.set_start_signal(_start_signal)
            _end_signal = self.signals[_end_signal_uuid]
            _fahrweg_obj.set_end_signal(_end_signal)

            _running_track_edge_ids = []

            # First edge
            _cur_track = None
            _cur_dir = _start_signal.wirkrichtung
            if _cur_dir == "in":
                # "in" direction
                _cur_track = _start_signal.right_track
                _running_track_edge_ids.append(_start_signal.left_track.id)  # To start train before signal
                _running_track_edge_ids.append(_cur_track.id)
            else:  # "gegen" direction
                _cur_track = _start_signal.left_track
                _running_track_edge_ids.append(_start_signal.right_track.re_id)  # To start train before signal
                _running_track_edge_ids.append(_cur_track.re_id)

            # Walk through edges
            while _cur_track is not None:
                # Get next point
                _next_point = _cur_track.right_point
                if _cur_dir == "gegen":
                    _next_point = _cur_track.left_point

                if _next_point.id == _end_signal.id:  # End signal found
                    break

                if _next_point.is_point():
                    # Track switch
                    _cur_top_kante_uuid = _cur_track.top_kante_uuid
                    _next_track = None
                    for _top_kante_uuid in _all_top_kanten_uuids:
                        if _top_kante_uuid != _cur_top_kante_uuid:
                            _next_track = _next_point.get_connected_node(_top_kante_uuid)
                            if _next_track is not None:
                                break

                    if _next_track is None:
                        raise ValueError("Data structure broken, no following TOP Kante found")

                    _cur_track = _next_track
                    if _cur_track.left_point.id == _next_point.id:
                        # "in" direction
                        _cur_dir = "in"
                    else:  # "gegen" direction
                        _cur_dir = "gegen"
                else:
                    # Only a signal
                    if _cur_dir == "in":
                        _cur_track = _next_point.right_track
                    else:
                        _cur_track = _next_point.left_track

                if _cur_dir == "in":
                    _running_track_edge_ids.append(_cur_track.id)
                else:
                    _running_track_edge_ids.append(_cur_track.re_id)

            _fahrweg_obj.tracks = _running_track_edge_ids
            return _fahrweg_obj


        if generate_running_tracks:
            running_tracks_as_json = generator.generate(self.plan_pro_file_name)
            print(running_tracks_as_json)
            running_tracks_list = json.loads(running_tracks_as_json)
            for running_track in running_tracks_list:
                start_signal_uuid = running_track["start_signal"]
                end_signal_uuid = running_track["end_signal"]
                all_top_kanten_uuids = []
                for edge in running_track["edges"]:
                    all_top_kanten_uuids.append(edge["edge_uuid"])
                fahrweg_uuid = str(uuid.uuid1())
                print(start_signal_uuid)
                print(end_signal_uuid)
                fahrweg_obj = process_running_track(fahrweg_uuid, start_signal_uuid, end_signal_uuid, all_top_kanten_uuids)
                print(fahrweg_obj)
                if fahrweg_obj is not None:
                    self.running_tracks[fahrweg_uuid] = fahrweg_obj
        else:
            for id_of_fachdaten in range(0, self.number_of_fachdaten):
                container = self.plan_pro_helper.get_container_by_fachdaten_id(id_of_fachdaten)
                for fstr_fahrweg in container.Fstr_Fahrweg:
                    fahrweg_uuid = fstr_fahrweg.Identitaet.Wert
                    start_signal_uuid = fstr_fahrweg.ID_Start.Wert
                    end_signal_uuid = fstr_fahrweg.ID_Ziel.Wert
                    all_top_kanten_uuids = []
                    for teilbereich in fstr_fahrweg.Bereich_Objekt_Teilbereich:
                        all_top_kanten_uuids.append(teilbereich.ID_TOP_Kante.Wert)

                    fahrweg_obj = process_running_track(fahrweg_uuid, start_signal_uuid, end_signal_uuid, all_top_kanten_uuids)
                    if fahrweg_obj is not None:
                        self.running_tracks[fahrweg_uuid] = fahrweg_obj
        return self.running_tracks

    def write_output(self, output_format="sumo-plain-xml"):
        output_helper = None
        if output_format == "sumo-plain-xml":
            output_helper = SUMOHelper(self.plan_pro_file_name)
        if output_helper is None:
            raise NotImplementedError()
        output_helper.create_output(self)
